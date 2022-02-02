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

from rest_framework import routers, viewsets
from rest_framework.request import QueryDict
from rest_framework.response import Response
from concurrent.futures import ThreadPoolExecutor

from django.core.mail import EmailMultiAlternatives
from django.shortcuts import redirect, render
from django.template.loader import get_template
from django.utils.crypto import get_random_string
from django.utils.translation import gettext_lazy as _

from .authentication import *
from .forms import KeyRequestForm
from .metadata import *
from .models import PendingApiUser
from .serializers import *

from chatnoir_search_v1.search import SimpleSearch, PhraseSearch


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
        return api_exception_handler(exceptions.NotFound(), None)

    def head(self, _):
        return Response(status=404)

    def list(self, _):
        raise exceptions.NotFound()

    def options(self, _, *args, **kwargs):
        raise exceptions.NotFound()


class ApiViewSet(viewsets.ViewSet):
    serializer_class = ApiSerializer
    metadata_class = ApiMetadata

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pretty_print = False

    def get_serializer(self, **kwargs):
        return self.serializer_class(**kwargs)

    def initialize_request(self, request, *args, **kwargs):
        request = super().initialize_request(request, *args, **kwargs)
        self.pretty_print = bool_param_set('pretty', request.data) or bool_param_set('pretty', request.GET)
        return request

    def get_renderer_context(self):
        context = super().get_renderer_context()
        if self.pretty_print and 'indent' not in context:
            context['indent'] = 4
        return context

    def list(self, request, **kwargs):
        raise exceptions.MethodNotAllowed(request.method)

    def post(self, request, **kwargs):
        raise exceptions.MethodNotAllowed(request.method)

    def put(self, request, **kwargs):
        raise exceptions.MethodNotAllowed(request.method)


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

    def _process_search(self, search_obj, request, params):
        serp_ctx = search_obj.search(params.data['query'])
        return Response(serp_ctx.to_dict(hits=True, meta=True, meta_extra=False))

    def post(self, request, **kwargs):
        params = SimpleSearchRequestSerializer(data=self._get_request_params(request))
        params.is_valid(raise_exception=True)
        validated = params.validated_data
        search = SimpleSearch(validated['index'], validated['from'], validated['size'], validated['explain'])
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
                },
                'comment': api_key.comment
            })

        except ApiKey.DoesNotExist:
            raise exceptions.ValidationError(_('Invalid API key.'))


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
            raise exceptions.ValidationError(
                _('API key "{}" does not exist or is not a sub key.').format(child))

    def put(self, request, target_apikey=None, **kwargs):
        if not target_apikey:
            raise exceptions.ValidationError(_('No target API given.'))

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
            raise exceptions.ValidationError(_('No target API given.'))

        api_key = self.check_is_sub_key(target_apikey, request.auth.api_key)
        api_key.revoked = True
        api_key.save()

        return Response({
            'message': _('API key revoked.'),
            'apikey': api_key.api_key
        })


send_mail_executor = ThreadPoolExecutor(max_workers=20)


def management_index(request):
    """API key management frontend index."""
    if request.method == 'POST':
        form = KeyRequestForm(request.POST)

        if form.is_valid():
            activation_code = get_random_string(length=36)
            try:
                instance = PendingApiUser.objects.get(email=form.cleaned_data['email'],
                                                      passcode=form.cleaned_data['passcode'])
                form.update_instance(instance, activation_code)
            except PendingApiUser.DoesNotExist:
                instance = form.save(commit=False)
                instance.activation_code = activation_code
                instance.save()

            mail_context = {
                'activation_code': activation_code
            }
            mail_content_plain = get_template('apikey_email/confirmation_email.txt').render(mail_context, request)
            mail_content_html = get_template('apikey_email/confirmation_email.html').render(mail_context, request)
            mail = EmailMultiAlternatives(
                _('Complete your %(appname)s API key request') % {'appname': settings.APPLICATION_NAME},
                mail_content_plain,
                settings.EMAIL_SENDER_ADDRESS,
                [instance.email]
            )
            mail.attach_alternative(mail_content_html, 'text/html')
            send_mail_executor.submit(mail.send)

            return redirect('apikey_management:request_sent')
    else:
        form = KeyRequestForm()

    return render(request, 'index.html', {'form': form})


def management_request_sent(request):
    """API key management frontend: API key request sent confirmation."""
    return render(request, 'apikey_frontend/request_sent.html', {})


def management_activate(request, activation_code):
    """API key management frontend: activate API key."""
    context = {}

    user = PendingApiUser.activate_by_code(activation_code)
    if user:
        user, api_key = user
        context['api_key'] = api_key

        mail_content_plain = get_template('apikey_email/apikey_email.txt').render(context, request)
        mail_content_html = get_template('apikey_email/apikey_email.html').render(context, request)
        mail = EmailMultiAlternatives(
            _('Your %(appname)s API key') % {'appname': settings.APPLICATION_NAME},
            mail_content_plain,
            settings.EMAIL_SENDER_ADDRESS,
            [user.email]
        )
        mail.attach_alternative(mail_content_html, 'text/html')
        send_mail_executor.submit(mail.send)

    return render(request, 'apikey_frontend/activate.html', context)
