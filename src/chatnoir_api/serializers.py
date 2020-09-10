from django.conf import settings
from rest_framework import serializers

from .validators import *


class OptionalListField(serializers.ListField):
    """
    List field accepting a single non-list value of type(child) as a single-item list.
    """

    def to_internal_value(self, data):
        if isinstance(data, (str, serializers.Mapping)) or not hasattr(data, '__iter__'):
            data = [data]
        return super().to_internal_value(data)


class ApiSerializer(serializers.Serializer):
    def get_fields(self):
        """
        :return: declared field names, but with trailing underscores stripped
        """
        return {k.rstrip('_'): v for k, v in super().get_fields().items()}


class AuthenticatedApiSerializer(ApiSerializer):
    apikey = serializers.CharField(
        required=True,
        max_length=255,
        initial='<apikey>',
        label='API Key',
        help_text='API key'
    )


class SimpleSearchRequestSerializerV1(AuthenticatedApiSerializer):
    query = serializers.CharField(
        required=True,
        initial='hello world',
        help_text='Search query'
    )
    index = OptionalListField(
        child=serializers.CharField(),
        required=False,
        initial=(settings.SEARCH_DEFAULT_INDEXES[1],),
        default=(settings.SEARCH_DEFAULT_INDEXES[1],),
        validators=(validate_index_names,),
        help_text='Index name or list of index names to search'
    )
    from_ = serializers.IntegerField(
        required=False,
        initial=0,
        default=0,
        help_text='Result list pagination begin'
    )
    size = serializers.IntegerField(
        required=False,
        initial=10,
        default=10,
        help_text='Number of results per page'
    )
    minimal = serializers.BooleanField(
        required=False,
        default=False,
        help_text='Reduce result list to score, uuid, target_uri, and snippet for each hit'
    )
    explain = serializers.BooleanField(
        required=False,
        default=False,
        help_text='Return additional scoring information'
    )


class PhraseSearchRequestSerializerV1(SimpleSearchRequestSerializerV1):
    slop = serializers.IntegerField(
        min_value=0,
        max_value=2,
        initial=0,
        default=0,
        required=False,
        help_text='How far terms in a phrase may be apart'
    )


class ResultMetaSerializerV1(ApiSerializer):
    query_time = serializers.IntegerField(
        help_text='Query time in milliseconds'
    )
    total_results = serializers.IntegerField(
        help_text='Total number of results'
    )
    indexes = serializers.ListField(
        child=serializers.CharField(),
        help_text='List of indexes that were searched'
    )


class ResultSerializerV1(ApiSerializer):
    score = serializers.FloatField(
        help_text='Ranking score of this result'
    )
    uuid = serializers.UUIDField(
        format='hex_verbose',
        help_text='Webis UUID of this document'
    )
    index = serializers.CharField(
        required=False,
        help_text='Index the document was retrieved from'
    )
    trec_id = serializers.CharField(
        allow_null=True,
        required=False,
        help_text='TREC ID of the result if available (null otherwise)'
    )
    target_hostname = serializers.CharField(
        required=False,
        help_text='Web host this document was crawled from'
    )
    target_uri = serializers.URLField(
        help_text='Full web URI'
    )
    page_rank = serializers.FloatField(
        allow_null=True,
        required=False,
        help_text='Page rank of this document if available (null otherwise)'
    )
    spam_rank = serializers.IntegerField(
        allow_null=True,
        required=False,
        help_text='Spam rank of this document if available (null otherwise)'
    )
    title = serializers.CharField(
        allow_blank=True,
        required=False,
        help_text='Document title with highlights'
    )
    snippet = serializers.CharField(
        allow_blank=True,
        help_text='Document body snippet with highlights'
    )


class ResultListSerializerV1(ApiSerializer):
    meta = ResultMetaSerializerV1(
        help_text='Global result meta information'
    )
    results = ResultSerializerV1(
        many=True,
        help_text='List of search results'
    )
