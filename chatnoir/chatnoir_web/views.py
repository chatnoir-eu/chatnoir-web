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


from django.conf import settings
from django.http import HttpResponsePermanentRedirect, HttpResponseBadRequest, JsonResponse
from django.middleware.csrf import get_token
from django.shortcuts import render
from django.views.decorators.http import require_http_methods, require_safe

from .middleware import time_limited_csrf
from chatnoir_search_v1.search import SimpleSearch
from chatnoir_api_v1.views import bool_param_set


@require_safe
def index(request):
    s = SimpleSearch(indices=request.GET.getlist('index'))
    allowed_indices = s.allowed_indices
    selected_indices = s.selected_indices

    ctx = dict(
        indices=[dict(id=k, name=v.get('display_name'), selected=k in selected_indices)
                 for k, v in allowed_indices.items()]
    )
    return render(request, 'index.html', ctx)


@require_safe
def cache(request):
    cache_url = settings.CACHE_FRONTEND_URL + '?' + request.GET.urlencode()
    return HttpResponsePermanentRedirect(cache_url)


@require_http_methods(['POST'])
@time_limited_csrf
def search(request):
    query_string = request.GET.get('q')

    if not query_string:
        return HttpResponseBadRequest('Missing search query.')

    page_num = request.GET.get('p', '1')
    if not page_num.isdigit():
        page_num = '1'
    page_num = max(0, int(page_num))

    indexes = request.GET.getlist('index')

    search = SimpleSearch(indexes, search_from=(page_num - 1) * 10, num_results=10,
                          explain=bool_param_set('explain', request.GET))
    search.explain = bool_param_set('explain', request.GET)
    serp_context = search.search(query_string)

    return JsonResponse(serp_context.to_dict(hits=True, meta=True, meta_extra=True),
                        headers={settings.CSRF_HEADER_SET_NAME: get_token(request)})
