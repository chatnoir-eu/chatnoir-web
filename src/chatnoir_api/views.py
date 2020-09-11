from rest_framework import routers, viewsets
from rest_framework.request import QueryDict
from rest_framework.response import Response

from .authentication import *
from .metadata import *
from .serializers import *

from chatnoir_search.search import SimpleSearchV1, PhraseSearchV1


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


def bool_param_set(name, request_params):
    return ImplicitBooleanField().to_internal_value(request_params.get(name, False))


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

    def initialize_request(self, request, *args, **kwargs):
        request = super().initialize_request(request, *args, **kwargs)
        self.pretty_print = bool_param_set('pretty', request.data) or bool_param_set('pretty', request.GET)
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

    def _get_request_params(self, request):
        data = request.data
        if isinstance(data, QueryDict):
            data = data.dict()

        if 'q' in data and 'query' not in data:
            data['query'] = request.data.pop('q')
        if 'i' in data and 'index' not in data:
            data['index'] = data.pop('i')
        if 'index' in data and type(data['index']) is str:
            data['index'] = data['index'].split(',')

        return data

    def _process_search(self, search_obj, request, params):
        serp_ctx = search_obj.search(params.data['query'])

        # keep API response compatible
        indexes_key = 'indices' if (request.auth and request.auth.is_legacy_key) else 'indexes'
        return Response({
            'meta': {
                'query_time': serp_ctx.query_time,
                'total_results': serp_ctx.total_results,
                indexes_key: list(serp_ctx.search.indexes.keys())
            },
            'results': serp_ctx.results_api
        })

    def post(self, request):
        params = SimpleSearchRequestSerializerV1(data=self._get_request_params(request))
        params.is_valid(raise_exception=True)
        validated = params.validated_data
        search = SimpleSearchV1(validated['index'], validated['from'], validated['size'], validated['explain'])
        search.minimal_response = validated['minimal']
        return self._process_search(search, request, params)


class PhraseSearchViewSetV1(SimpleSearchViewSetV1):
    """
    ChatNoir exact phrase search module.
    """

    serializer_class = PhraseSearchRequestSerializerV1

    def get_view_name(self):
        return 'Phrase Search'

    def post(self, request):
        params = PhraseSearchRequestSerializerV1(data=self._get_request_params(request))
        params.is_valid(raise_exception=True)
        validated = params.validated_data
        search = PhraseSearchV1(validated['index'], validated['from'], validated['size'],
                                validated['explain'], validated['slop'])
        search.minimal_response = validated['minimal']
        return self._process_search(search, request, params)
