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

import json
import time

from django.conf import settings
from django.core.mail import mail_managers
from django.http import HttpResponsePermanentRedirect, HttpResponseNotAllowed, JsonResponse, HttpResponse, Http404
from django.middleware.csrf import get_token
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.urls import resolve, reverse
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.views.decorators.http import require_safe, require_POST
from django.utils.translation import gettext_lazy as _

from chatnoir_api.authentication import ApiKeyAuthentication
from chatnoir_api.forms import KeyRequestForm
from chatnoir_api.models import ApiPendingUser, SEND_MAIL_EXECUTOR
from chatnoir_search.search import SimpleSearch
from .context_processors import _get_frontend_settings


# -----------------------
#    Main index view
# -----------------------

@ensure_csrf_cookie
def index(request):
    """Index view."""
    if request.method == 'HEAD':
        return HttpResponse(status=200)

    # Regular frontend token init request
    if (request.method == 'POST'
            and 'init' in request.GET
            and request.headers.get('X-Requested-With') == 'XMLHttpRequest'):
        return _init_frontend_session(request)

    # Vite dev server init request for CSRF token and settings
    if (settings.DEBUG
            and request.method == 'GET'
            and 'init-dev' in request.GET
            and request.headers.get('X-Requested-With') == 'XMLHttpRequest'
            and request.headers.get('Origin') in settings.CSRF_TRUSTED_ORIGINS):
        return JsonResponse(_get_frontend_settings())

    # Regular GET request
    if request.method == 'GET':
        return render(request, 'index.html')

    return HttpResponseNotAllowed(permitted_methods=['GET'])


@csrf_protect
def _init_frontend_session(request):
    apikey = ApiKeyAuthentication.issue_temporary_session_apikey(request, issuer='web_frontend')
    return JsonResponse({
        'token': {
            'token': apikey.api_key,
            'timestamp': int(apikey.issue_date.timestamp()),
            'max_age': int((apikey.expires - apikey.issue_date).total_seconds()) + 1,
            'quota': apikey.limits_day
        },
        'timestamp': int(time.time()),
        'csrfToken': get_token(request),
        'indices': _get_indices(request)
    })


def _get_indices(request):
    """List of configured indices."""
    search = SimpleSearch(indices=request.GET.getlist('index'))
    selected = search.selected_indices
    return [{'id': k, 'name': v.get('display_name'), 'source_url': v.get('source_url'), 'selected': k in selected}
            for k, v in search.allowed_indices.items()]


# ----------------------------
#    API key request pages
# ----------------------------

@ensure_csrf_cookie
def apikey_request_academic(request):
    """Request form view for academic API keys."""
    if request.method == 'GET':
        return index(request)
    return _apikey_request(request, False)


@ensure_csrf_cookie
def apikey_request_passcode(request):
    """Request form view for passcode-issued API keys."""
    if request.method == 'GET':
        return index(request)
    return _apikey_request(request, True)


@csrf_protect
@require_POST
def _apikey_request(request, passcode):
    form = KeyRequestForm(request.POST, passcode=passcode)

    if not form.is_valid():
        return JsonResponse({
            'valid': False,
            'errors': form.errors.get_json_data()
        })

    instance = form.save(commit=False)
    activation_code = instance.generate_activation_code(save=True)
    instance.send_verification_mail(
        request.build_absolute_uri(reverse('chatnoir_frontend:apikey_request_verify', args=[activation_code])))

    if passcode:
        return JsonResponse({
            'valid': True,
            'message': _('We have received your API key request. To complete the process, '
                         'please check your inbox and click the activation link contained in the email.')
        })

    return JsonResponse({
        'valid': True,
        'message': _('We have received your API key request and will review your application. '
                     'If approved, you will receive your API key within the next few days by email.')
    })


@require_safe
def apikey_request_verify(request, activation_code=None):
    """User email link verification view."""

    if not activation_code:
        return index(request)

    user = ApiPendingUser.verify_email_by_activation_code(activation_code)
    if user is None:
        # Invalid code
        return redirect(reverse('chatnoir_frontend:apikey_request_verify_index') + '?error=invalid+code')
    if user is False:
        # Already activated
        return redirect(reverse('chatnoir_frontend:apikey_request_verify_index') + '?already_verified')

    # Activate user instantly if they have a passcode, otherwise notify managers
    if user.passcode:
        user.activate(send_email=True)
    else:
        mail_context = {
            'app_name': settings.APPLICATION_NAME,
            'user': user,
        }
        SEND_MAIL_EXECUTOR.submit(mail_managers,
                                  _('New pending %(appname)s API key request') % {'appname': settings.APPLICATION_NAME},
                                  render_to_string('email/apikey_request_notification.txt', mail_context),
                                  fail_silently=True)

    query_string = f'?success'
    if user.passcode:
        query_string += '&passcode'
    return redirect(reverse('chatnoir_frontend:apikey_request_verify_index') + query_string)


# -----------------------
#        API Docs
# -----------------------
@require_safe
def docs(request):
    url_name = resolve(request.path_info).url_name
    context = None
    if url_name in ['docs_index', 'docs_api_general', 'docs_api_advanced', 'docs_api_advanced_management']:
        if url_name == 'docs_api_general':
            indices = _get_indices(request)
            context = {
                'indices': indices,
                'cache_frontend_url': settings.CACHE_FRONTEND_URL,
                'default_indices_json': json.dumps([i['id'] for i in indices
                                                    if settings.SEARCH_INDICES[i['id']].get('default', False)])
            }
        return render(request, f'docs/{url_name[5:]}.html', context=context)
    raise Http404


# -----------------------
#    Cache redirect
# -----------------------

@require_safe
def cache(request):
    cache_url = settings.CACHE_FRONTEND_URL + '?' + request.GET.urlencode()
    return HttpResponsePermanentRedirect(cache_url)
