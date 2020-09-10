from django.utils.translation import gettext as _
from rest_framework import routers, viewsets
from rest_framework.request import QueryDict
from rest_framework.response import Response

from .authentication import *
from .metadata import *
from .serializers import *

from chatnoir_search.search import SimpleSearchV1


def api_exception_handler(exc, _):
    if not isinstance(exc, exceptions.APIException):
        raise exc

    status_code = exc.status_code
    if isinstance(exc, (exceptions.NotAuthenticated, exceptions.AuthenticationFailed)):
        status_code = 401

    response = Response({
        'code': status_code,
        'message': exc.detail
    }, status_code)

    return response


class APIRootV1(routers.APIRootView):
    """
    REST API for accessing ChatNoir search results.
    """

    def get_view_name(self):
        return 'ChatNoir API'


class ApiViewSet(viewsets.ViewSet):
    serializer_class = SimpleSearchRequestSerializerV1
    metadata_class = SimpleSearchMetadata

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pretty_print = False

    def get_serializer(self):
        return self.serializer_class()

    @staticmethod
    def _bool_param_set(param, request_data):
        return param in request_data and str(request_data.get(param)).lower() not in ('0', 'false')

    def initialize_request(self, request, *args, **kwargs):
        request = super().initialize_request(request, *args, **kwargs)
        self.pretty_print = self._bool_param_set('pretty', request.data) or self._bool_param_set('pretty', request.GET)
        return request

    def get_renderer_context(self):
        context = super().get_renderer_context()
        if self.pretty_print and 'indent' not in context:
            context['indent'] = 4
        return context


class SimpleSearchViewSetV1(ApiViewSet):
    """
    Default ChatNoir search module.
    """

    # metadata_class = SimpleSearchMetadata
    allowed_methods = ('GET', 'POST', 'OPTIONS')
    authentication_classes = (ApiKeyAuthentication,)

    def get_view_name(self):
        return 'Simple Search'

    def list(self, request):
        request.data.update(request.GET.dict())
        return self.post(request)

    def post(self, request):
        data = request.data
        if isinstance(data, QueryDict):
            data = data.dict()

        if 'q' in data and 'query' not in data:
            data['query'] = request.data.pop('q')
        if 'i' in data and 'index' not in data:
            data['index'] = data.pop('i')
        if 'index' in data and type(data['index']) is str:
            data['index'] = data['index'].split(',')

        params = SimpleSearchRequestSerializerV1(data=data)
        params.is_valid(raise_exception=True)

        serp_ctx = SimpleSearchV1(params.data['index'], params.data['from']).search(params.data['query'])
        return Response({
            'meta': {
                'query_time': serp_ctx.query_time,
                'total_results': serp_ctx.total_results,
                'indices': params.data['index']
            },
            'results': serp_ctx.results_api
        })


class PhraseSearchViewSetV1(SimpleSearchViewSetV1):
    """
    ChatNoir exact phrase search module.
    """

    serializer_class = PhraseSearchRequestSerializerV1

    def get_view_name(self):
        return 'Phrase Search'
