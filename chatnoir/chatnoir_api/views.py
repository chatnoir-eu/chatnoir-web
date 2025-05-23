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

from hashlib import sha256

from django.utils.translation import gettext_lazy as _
import elasticsearch
from rest_framework import routers, viewsets, exceptions as rest_exceptions
from rest_framework.request import QueryDict
from rest_framework.response import Response
from rest_framework.status import HTTP_504_GATEWAY_TIMEOUT

from .authentication import ApiKeyAuthentication, HasKeyCreateRole
from .metadata import ApiMetadata
from .serializers import *

from chatnoir_search.search import SimpleSearch, PhraseSearch


def api_exception_handler(exc, _):
    if not isinstance(exc, rest_exceptions.APIException):
        raise exc

    status_code = exc.status_code
    if isinstance(exc, (rest_exceptions.NotAuthenticated, rest_exceptions.AuthenticationFailed)):
        # Django "corrects" these codes to 403, since API keys do not rely on the Django authentication middleware
        status_code = 401

    return Response({
        'code': status_code,
        'error': exc.get_codes(),
        'message': exc.detail
    }, status_code)


def bool_param_set(name, request_params):
    try:
        return ImplicitBooleanField().to_internal_value(request_params.get(name, False))
    except rest_exceptions.ValidationError:
        return False


class APIRoot(routers.APIRootView):
    __doc__ = _('%(appname)s REST API') % {'appname': settings.APPLICATION_NAME}

    def get_view_name(self):
        return _(settings.APPLICATION_NAME)

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        return Response({k: v for k, v in response.data.items()
                         if '/' not in k and k != '.+'}, status=response.status_code)


class Error404(viewsets.ViewSet):
    allowed_methods = tuple()

    def get_view_name(self):
        return _('Not Found')

    def handle_exception(self, _):
        return api_exception_handler(rest_exceptions.NotFound(), None)

    def head(self, _):
        return Response(status=404)

    def list(self, _):
        raise rest_exceptions.NotFound()

    def options(self, _, *args, **kwargs):
        raise rest_exceptions.NotFound()


class ApiViewSet(viewsets.ViewSet):
    serializer_class = ApiSerializer
    metadata_class = ApiMetadata

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pretty_print = False

    def get_serializer(self, **kwargs):
        return self.serializer_class(**kwargs)

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        self.pretty_print = bool_param_set('pretty', request.data) or bool_param_set('pretty', request.GET)

    def get_renderer_context(self):
        context = super().get_renderer_context()
        if self.pretty_print and 'indent' not in context:
            context['indent'] = 4
        return context

    def list(self, request, **kwargs):
        raise rest_exceptions.MethodNotAllowed(request.method)

    def post(self, request, **kwargs):
        raise rest_exceptions.MethodNotAllowed(request.method)

    def put(self, request, **kwargs):
        raise rest_exceptions.MethodNotAllowed(request.method)


class SimpleSearchViewSet(ApiViewSet):
    __doc__ = _('Default %(appname)s search API') % {'appname': settings.APPLICATION_NAME}

    serializer_class = SimpleSearchRequestSerializer
    allowed_methods = ('GET', 'POST', 'OPTIONS')
    authentication_classes = (ApiKeyAuthentication,)

    def get_view_name(self):
        return _('Simple Search')

    def list(self, request, **kwargs):
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

    def _log_query(self, search_obj, request, query):
        """Log a search query using the configured query logging facility."""

        fields = {}
        if request.auth:
            for r in request.auth.roles.values('role'):
                if r['role'] == settings.API_NOLOG_ROLE:
                    return

            fields['user'] = {
                'name': request.auth.user.common_name if request.auth.user else '<anonymous>',
                'hash': sha256(request.auth.api_key.encode()).hexdigest(),
                'issuer': request.auth.issuer,
            }

        search_obj.log_query(query, extra=fields)

    def _process_search(self, search_obj, request, params):
        """Run the search using the selected search class."""
        self._log_query(search_obj, request, params.data['query'])
        try:
            serp_ctx = search_obj.search(params.data['query'])
        except elasticsearch.ConnectionTimeout:
            raise rest_exceptions.APIException(_('The search backend took too long to respond.',
                                                 code=HTTP_504_GATEWAY_TIMEOUT), 'timeout')
        serp_ctx = serp_ctx.to_dict(results=True, meta=True, extended_meta=params.data.get('_extended_meta', False))

        if hasattr(search_obj, 'search_method') and 'meta' in serp_ctx:
            serp_ctx['meta']['search_method'] = search_obj.search_method

        return Response(serp_ctx)

    def post(self, request, **kwargs):
        params = SimpleSearchRequestSerializer(data=self._get_request_params(request))
        params.is_valid(raise_exception=True)
        validated = params.validated_data
        search = SimpleSearch(validated['index'],
                              validated['from'],
                              validated['size'],
                              validated['explain'],
                              validated.get('search_method'))
        search.minimal_response = validated['minimal']
        return self._process_search(search, request, params)


class PhraseSearchViewSet(SimpleSearchViewSet):
    __doc__ = _('%(appname)s exact phrase search API') % {'appname': settings.APPLICATION_NAME}

    serializer_class = PhraseSearchRequestSerializer

    def get_view_name(self):
        return _('Phrase Search')

    def post(self, request, **kwargs):
        params = PhraseSearchRequestSerializer(data=self._get_request_params(request))
        params.is_valid(raise_exception=True)
        validated = params.validated_data
        search = PhraseSearch(validated['index'], validated['from'], validated['size'],
                              validated['explain'], validated['slop'])
        search.minimal_response = validated['minimal']
        return self._process_search(search, request, params)


class ManageKeysViewSet(ApiViewSet):
    __doc__ = _('%(appname)s API key management API') % {'appname': settings.APPLICATION_NAME}

    authentication_classes = (ApiKeyAuthentication,)

    def get_view_name(self):
        return _('API Key Management')


class ManageKeysInfoViewSet(ManageKeysViewSet):
    __doc__ = ManageKeysViewSet.__doc__

    serializer_class = SimpleSearchRequestSerializer
    allowed_methods = ('GET', 'OPTIONS')

    def list(self, request, **kwargs):
        try:
            api_key = ApiKey.objects.get(api_key=request.auth.api_key)
            user = api_key.user

            return Response({
                'apikey': api_key.api_key,
                'expires': api_key.expires,
                'revoked': api_key.revoked,
                'user': {
                    'common_name': user.common_name,
                    'email': user.email,
                    'organization': user.organization,
                    'address': user.address,
                    'zip_code': user.zip_code,
                    'state': user.state,
                    'country': user.country.code,
                },
                'roles': [r.role for r in api_key.roles.all()],
                'remote_hosts': api_key.allowed_remote_hosts_list,
                'limits': {
                    'day': api_key.limits_day,
                    'week': api_key.limits_week,
                    'month': api_key.limits_month,
                },
                'comment': api_key.comments
            })

        except ApiKey.DoesNotExist:
            raise rest_exceptions.ValidationError({'apikey': _('Invalid API key.')}, 'invalid_key')


class ManageKeysCreateViewSet(ManageKeysViewSet):
    __doc__ = ManageKeysViewSet.__doc__

    serializer_class = ApiKeySerializer
    permission_classes = (HasKeyCreateRole,)
    allowed_methods = ('POST', 'OPTIONS')

    def post(self, request, **kwargs):
        request_data = request.data.copy()
        if 'apikey' in request_data:
            request_data.pop('apikey')
        request_data['parent'] = request.auth.api_key
        request_data = ParentedApiKeySerializer(data=request_data)
        request_data.is_valid(raise_exception=True)
        api_key = request_data.save(request.auth)

        return Response({
            'message': _('API key created.'),
            'apikey': api_key.api_key
        })


class ManageKeysUpdateViewSet(ManageKeysViewSet):
    __doc__ = ManageKeysViewSet.__doc__

    serializer_class = ApiKeySerializer
    permission_classes = (HasKeyCreateRole,)
    allowed_methods = ('PUT', 'OPTIONS')

    @staticmethod
    def check_is_sub_key(child, parent):
        try:
            child_key = ApiKey.objects.get(api_key=child)
            if not child_key.is_sub_key_of(parent):
                raise ApiKey.DoesNotExist
            return child_key
        except ApiKey.DoesNotExist:
            raise rest_exceptions.ValidationError(
                {'apikey': _('API key "{}" does not exist or is not a sub key.').format(child)}, 'invalid_key')

    def put(self, request, target_apikey=None, **kwargs):
        if not target_apikey:
            raise rest_exceptions.ValidationError(_('No target API key given.'))

        self.check_is_sub_key(target_apikey, request.auth.api_key)

        request_data = request.data.copy()

        if 'parent' in request_data:
            request_data.pop('parent')
        request_data = ApiKeySerializer(data=request_data)
        request_data.is_valid(raise_exception=True)

        api_key = request_data.save()

        return Response({
            'message': _('API key updated.'),
            'apikey': api_key.api_key
        })


class ManageKeysRevokeViewSet(ManageKeysUpdateViewSet):
    __doc__ = ManageKeysUpdateViewSet.__doc__

    serializer_class = ApiKeyRevocationSerializer

    def put(self, request, target_apikey=None, **kwargs):
        if not target_apikey:
            raise rest_exceptions.ValidationError(_('No target API given.'))

        api_key = self.check_is_sub_key(target_apikey, request.auth.api_key)
        api_key.revoked = True
        api_key.save()

        return Response({
            'message': _('API key revoked.'),
            'apikey': api_key.api_key
        })
