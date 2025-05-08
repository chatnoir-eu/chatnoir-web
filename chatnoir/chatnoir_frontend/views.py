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

import time

from django.conf import settings
from django.http import HttpResponsePermanentRedirect, HttpResponseNotAllowed, JsonResponse, HttpResponse
from django.middleware.csrf import get_token
from django.shortcuts import render
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie, requires_csrf_token
from django.views.decorators.http import require_safe

from chatnoir_api.authentication import ApiKeyAuthentication
from chatnoir_search.search import SimpleSearch


@ensure_csrf_cookie
def index(request):
    if request.method == 'HEAD':
        return HttpResponse(status=200)

    if (request.method == 'POST'
            and 'init' in request.GET
            and request.headers.get('X-Requested-With') == 'XMLHttpRequest'):
        return _init_frontend_session(request)

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
    return [{'id': k, 'name': v.get('display_name'), 'selected': k in selected}
            for k, v in search.allowed_indices.items()]


@require_safe
def cache(request):
    cache_url = settings.CACHE_FRONTEND_URL + '?' + request.GET.urlencode()
    return HttpResponsePermanentRedirect(cache_url)
