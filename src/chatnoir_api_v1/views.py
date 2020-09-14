from django.utils.translation import gettext as _
from rest_framework import routers, viewsets
from rest_framework.request import QueryDict
from rest_framework.response import Response

from .authentication import *
from .metadata import *
from .serializers import *

from .search import SimpleSearch, PhraseSearch


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


class APIRoot(routers.APIRootView):
    """
    REST API for accessing ChatNoir search results.
    """

    def get_view_name(self):
        return _('ChatNoir API')


class ApiViewSet(viewsets.ViewSet):
    serializer_class = SimpleSearchRequestSerializer
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


class SimpleSearchViewSet(ApiViewSet):
    """
    Default ChatNoir search module.
    """

    # metadata_class = SimpleSearchMetadata
    allowed_methods = ('GET', 'POST', 'OPTIONS')
    authentication_classes = (ApiKeyAuthentication,)

    def get_view_name(self):
        return _('Simple Search')

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
        params = SimpleSearchRequestSerializer(data=self._get_request_params(request))
        params.is_valid(raise_exception=True)
        validated = params.validated_data
        search = SimpleSearch(validated['index'], validated['from'], validated['size'], validated['explain'])
        search.minimal_response = validated['minimal']
        return self._process_search(search, request, params)


class PhraseSearchViewSet(SimpleSearchViewSet):
    """
    ChatNoir exact phrase search module.
    """

    serializer_class = PhraseSearchRequestSerializer

    def get_view_name(self):
        return _('Phrase Search')

    def post(self, request):
        params = PhraseSearchRequestSerializer(data=self._get_request_params(request))
        params.is_valid(raise_exception=True)
        validated = params.validated_data
        search = PhraseSearch(validated['index'], validated['from'], validated['size'],
                              validated['explain'], validated['slop'])
        search.minimal_response = validated['minimal']
        return self._process_search(search, request, params)


class ManageKeysInfoViewSet(ApiViewSet):
    """
    API key management endpoint.
    """

    authentication_classes = (ApiKeyAuthentication,)
    allowed_methods = ('GET',)

    def get_view_name(self):
        return _('API Key Management')

    def list(self, request):
        try:
            api_key = ApiKey.objects.get(api_key=request.auth.api_key)
            limits = api_key.limits_inherited
            user = api_key.user

            return Response({
                'apikey': api_key.api_key,
                'expires': api_key.expires_inherited,
                'revoked': api_key.is_revoked,
                'user': {
                    'common_name': user.common_name,
                    'email': user.email,
                    'organization': user.organization,
                    'address': user.address,
                    'zip_code': user.zip_code,
                    'state': user.state,
                    'country': user.country,
                },
                'roles': [r.role for r in api_key.roles.all()],
                'remote_hosts': api_key.allowed_remote_hosts_list,
                'limits': {
                    'day': limits[0],
                    'week': limits[1],
                    'month': limits[2],
                }
            })

        except ApiKey.DoesNotExist:
            raise exceptions.ValidationError(_('Invalid API key.'))
