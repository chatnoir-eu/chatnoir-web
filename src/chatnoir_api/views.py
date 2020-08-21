from rest_framework import routers, viewsets
from rest_framework.response import Response

from .metadata import *
from .serializers import *

from chatnoir_search.search import SimpleSearchV1


class APIRootV1(routers.APIRootView):
    """
    REST API for accessing ChatNoir search results.
    """

    def get_view_name(self):
        return 'ChatNoir API'


class ApiViewSet(viewsets.ViewSet):
    serializer_class = SimpleSearchRequestSerializerV1
    metadata_class = SimpleSearchMetadata

    def get_serializer(self):
        return self.serializer_class()


class SimpleSearchViewSetV1(ApiViewSet):
    """
    Default ChatNoir search module.
    """

    # metadata_class = SimpleSearchMetadata
    allowed_methods = ('GET', 'POST', 'OPTIONS')

    def get_view_name(self):
        return 'Simple Search'

    def list(self, request):
        return Response({'query': 'foo'})

    def post(self, request):
        params = SimpleSearchRequestSerializerV1(data=request.data)
        params.is_valid(raise_exception=True)

        serp_context = SimpleSearchV1(params.data['index'], params.data['from']).search(params.data['query'])
        # TODO: implement proper validation and results serialization
        return Response({})


class PhraseSearchViewSetV1(SimpleSearchViewSetV1):
    """
    ChatNoir exact phrase search module.
    """

    serializer_class = PhraseSearchRequestSerializerV1

    def get_view_name(self):
        return 'Phrase Search'
