from django.conf import settings
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from chatnoir_apikey_management.models import *
from .validators import *


class OptionalListField(serializers.ListField):
    """
    List field accepting a single non-list value of type(child) as a single-item list.
    """

    def to_internal_value(self, data):
        if isinstance(data, (str, serializers.Mapping)) or not hasattr(data, '__iter__'):
            data = [data]
        return super().to_internal_value(data)


class ImplicitBooleanField(serializers.BooleanField):
    """
    Boolean field that treats no or an empty value as True.
    """
    TRUE_VALUES = serializers.BooleanField.TRUE_VALUES | {'', None}
    NULL_VALUES = {}


class ApiSerializer(serializers.Serializer):
    def get_fields(self):
        """
        :return: declared field names, but with trailing underscores stripped
        """
        return {k.rstrip('_'): v for k, v in super().get_fields().items()}


class ApiModelSerializer(ApiSerializer, serializers.ModelSerializer):
    pass


class AuthenticatedApiSerializer(ApiSerializer):
    apikey = serializers.CharField(
        required=True,
        max_length=255,
        initial=_('<apikey>'),
        label=_('API Key'),
        help_text=_('API key')
    )


class SimpleSearchRequestSerializerV1(AuthenticatedApiSerializer):
    query = serializers.CharField(
        required=True,
        initial=_('hello world'),
        help_text=_('Search query')
    )
    index = OptionalListField(
        child=serializers.CharField(),
        required=False,
        initial=(settings.SEARCH_DEFAULT_INDEXES[1],),
        default=(settings.SEARCH_DEFAULT_INDEXES[1],),
        validators=(validate_index_names,),
        help_text=_('Index name or list of index names to search')
    )
    from_ = serializers.IntegerField(
        required=False,
        initial=0,
        default=0,
        help_text=_('Result list pagination begin')
    )
    size = serializers.IntegerField(
        required=False,
        initial=10,
        default=10,
        help_text=_('Number of results per page')
    )
    minimal = ImplicitBooleanField(
        required=False,
        default=False,
        help_text=_('Reduce result list to score, uuid, target_uri, and snippet for each hit')
    )
    explain = ImplicitBooleanField(
        required=False,
        default=False,
        help_text=_('Return additional scoring information')
    )


class PhraseSearchRequestSerializerV1(SimpleSearchRequestSerializerV1):
    slop = serializers.IntegerField(
        min_value=0,
        max_value=2,
        initial=0,
        default=0,
        required=False,
        help_text=_('How far terms in a phrase may be apart')
    )


class ResultMetaSerializerV1(ApiSerializer):
    query_time = serializers.IntegerField(
        help_text=_('Query time in milliseconds')
    )
    total_results = serializers.IntegerField(
        help_text=_('Total number of results')
    )
    indexes = serializers.ListField(
        child=serializers.CharField(),
        help_text=_('List of indexes that were searched')
    )


class ResultSerializerV1(ApiSerializer):
    score = serializers.FloatField(
        help_text=_('Ranking score of this result')
    )
    uuid = serializers.UUIDField(
        format='hex_verbose',
        help_text=_('Webis UUID of this document')
    )
    index = serializers.CharField(
        required=False,
        help_text=_('Index the document was retrieved from')
    )
    trec_id = serializers.CharField(
        allow_null=True,
        required=False,
        help_text=_('TREC ID of the result if available (null otherwise)')
    )
    target_hostname = serializers.CharField(
        required=False,
        help_text=_('Web host this document was crawled from')
    )
    target_uri = serializers.URLField(
        help_text='Full web URI'
    )
    page_rank = serializers.FloatField(
        allow_null=True,
        required=False,
        help_text=_('Page rank of this document if available (null otherwise)')
    )
    spam_rank = serializers.IntegerField(
        allow_null=True,
        required=False,
        help_text=_('Spam rank of this document if available (null otherwise)')
    )
    title = serializers.CharField(
        allow_blank=True,
        required=False,
        help_text=_('Document title with highlights')
    )
    snippet = serializers.CharField(
        allow_blank=True,
        help_text=_('Document body snippet with highlights')
    )


class ResultListSerializerV1(ApiSerializer):
    meta = ResultMetaSerializerV1(
        help_text=_('Global result meta information')
    )
    results = ResultSerializerV1(
        many=True,
        help_text=_('List of search results')
    )


class ApiUserSerializer(ApiModelSerializer):
    class Meta:
        model = ApiUser
        fields = ['common_name', 'email', 'organization', 'address', 'zip_code', 'state', 'country']
        extra_kwargs = {
            'email': {
                'validators': [],
            }
        }


class ApiLimitsSerializer(ApiSerializer):
    day = serializers.IntegerField(allow_null=True, required=True)
    week = serializers.IntegerField(allow_null=True, required=True)
    month = serializers.IntegerField(allow_null=True, required=True)


class ApiKeySerializer(ApiSerializer):
    class Meta:
        validators = (validate_api_key,)

    apikey = serializers.CharField(
        required=False,
        max_length=255,
        label=_('API Key'),
        help_text=_('API key')
    )
    parent = serializers.CharField(
        required=False,
        max_length=255,
        label=_('Parent Key'),
        help_text=_('Parent key')
    )
    user = ApiUserSerializer(required=True)
    roles = serializers.ListSerializer(
        child=serializers.CharField(max_length=255, validators=(validate_api_role_exists,)),
        allow_empty=True,
        allow_null=True,
        required=False
    )
    limits = ApiLimitsSerializer(required=True)
    remote_hosts = serializers.ListSerializer(
        child=serializers.CharField(max_length=255, validators=(validate_cidr_address,)),
        allow_empty=True,
        allow_null=True,
        required=False
    )
    expires = serializers.DateField(allow_null=True, required=False)

    def save(self):
        user, _ = ApiUser.objects.update_or_create(email=self.validated_data['user']['email'],
                                                   defaults=self.validated_data['user'])

        api_key_defaults = dict(
            user=user,
            limits_day=self.validated_data['limits']['day'],
            limits_week=self.validated_data['limits']['week'],
            limits_month=self.validated_data['limits']['month'],
            allowed_remote_hosts=','.join(self.validated_data['remote_hosts']),
            expires=self.validated_data['expires']
        )

        api_key = self.validated_data.get('apikey')
        if api_key:
            api_key, _ = ApiKey.objects.update_or_create(
                api_key=self.validated_data['apikey'], defaults=api_key_defaults)
        else:
            api_key = ApiKey.objects.create(**api_key_defaults)

        return api_key
