# Copyright 2021 Janek Bevendorff
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from functools import partial

from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from .models import *
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


class SimpleSearchRequestSerializer(AuthenticatedApiSerializer):
    query = serializers.CharField(
        required=True,
        initial=_('hello world'),
        help_text=_('Search query')
    )
    index = OptionalListField(
        child=serializers.CharField(),
        required=False,
        initial=[k for k, v in settings.SEARCH_INDICES.items() if v.get('default')],
        default=[k for k, v in settings.SEARCH_INDICES.items() if v.get('default')],
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


class PhraseSearchRequestSerializer(SimpleSearchRequestSerializer):
    slop = serializers.IntegerField(
        min_value=0,
        max_value=2,
        initial=0,
        default=0,
        required=False,
        help_text=_('How far terms in a phrase may be apart')
    )


class ResultMetaSerializer(ApiSerializer):
    query_time = serializers.IntegerField(
        help_text=_('Query time in milliseconds')
    )
    total_results = serializers.IntegerField(
        help_text=_('Total number of results')
    )
    indices = serializers.ListField(
        child=serializers.CharField(),
        help_text=_('List of indices that were searched')
    )


class ResultSerializer(ApiSerializer):
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


class ResultListSerializer(ApiSerializer):
    meta = ResultMetaSerializer(
        help_text=_('Global result meta information')
    )
    results = ResultSerializer(
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
        validators = (partial(validate_api_key, no_parent_ok=True),)

    apikey = serializers.CharField(
        required=False,
        initial=_('<apikey>'),
        max_length=255,
        label=_('API Key'),
        help_text=_('API key')
    )
    user = ApiUserSerializer(required=True)
    roles = serializers.ListSerializer(
        child=serializers.CharField(max_length=255, validators=(validate_api_role_exists,)),
        allow_empty=True,
        allow_null=True,
        required=False
    )
    limits = ApiLimitsSerializer(required=False)
    remote_hosts = serializers.ListSerializer(
        child=serializers.CharField(max_length=255, validators=(validate_cidr_address,)),
        allow_empty=True,
        allow_null=True,
        required=False
    )
    expires = serializers.DateTimeField(allow_null=True, required=False)
    comment = serializers.CharField(allow_blank=True, required=False)

    def save(self, parent=None):
        user, _ = ApiUser.objects.update_or_create(email=self.validated_data['user']['email'],
                                                   defaults=self.validated_data['user'])

        limits = self.validated_data.get('limits', {})
        api_key_defaults = dict(
            user=user,
            limits_day=limits.get('day'),
            limits_week=limits.get('week'),
            limits_month=limits.get('month'),
            revoked=False,
            expires=self.validated_data.get('expires'),
            allowed_remote_hosts=','.join(self.validated_data.get('remote_hosts', '')),
            comment=self.validated_data.get('comment', '')
        )

        api_key = self.validated_data.get('apikey')
        if parent and parent != api_key:
            api_key_defaults['parent'] = parent

        if api_key:
            api_key, _ = ApiKey.objects.update_or_create(
                api_key=self.validated_data['apikey'], defaults=api_key_defaults)
        else:
            api_key = ApiKey.objects.create(**api_key_defaults)

        api_key.roles.set(ApiKeyRole.objects.filter(role__in=self.validated_data.get('roles', [])),)

        return api_key


class ParentedApiKeySerializer(ApiKeySerializer):
    class Meta:
        validators = (validate_api_key,)

    parent = serializers.CharField(
        required=False,
        max_length=255,
        label=_('Parent Key'),
        help_text=_('Parent key')
    )


class ApiKeyRevocationSerializer(ApiSerializer):
    class Meta:
        validators = (validate_api_key,)

    apikey = serializers.CharField(
        required=False,
        initial=_('<apikey>'),
        max_length=255,
        label=_('API Key'),
        help_text=_('API key')
    )
