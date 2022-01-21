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

import uuid

from django.conf import settings
from django.http import Http404, HttpResponseBadRequest, JsonResponse
from django.middleware.csrf import get_token
from django.shortcuts import HttpResponse, render
from django.views.decorators.http import require_http_methods, require_safe

from chatnoir_search_v1.cache import CacheDocument
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


def webis_uuid(prefix, doc_id):
    """
    Calculate Webis UUID from a corpus prefix and a document ID.
    """
    return str(uuid.uuid5(uuid.NAMESPACE_URL, ':'.join((prefix, doc_id))))


def cache(request):
    if 'index' not in request.GET or request.GET.get('index') not in settings.SEARCH_INDICES:
        raise Http404

    raw_mode = bool_param_set('raw', request.GET)
    plaintext_mode = bool_param_set('plain', request.GET)
    post_process_html = not bool_param_set('no-rewrite', request.GET)
    context = {
        'cache': {
            'index': request.GET.get('index'),
            'is_plaintext_mode': plaintext_mode,
            'is_raw_mode': raw_mode,
            'search_query': request.GET.get('q', ''),
            'search_page': request.GET.get('p', '')
        }
    }

    cache_doc = CacheDocument()
    doc_id = request.GET.get('uuid')
    if not doc_id and request.GET.get('trec-id'):
        # Retrieve by internal document ID, which is usually faster than searching for the warc_trec_id term
        doc_id = webis_uuid(settings.SEARCH_INDICES[request.GET['index']]['warc_uuid_prefix'], request.GET['trec-id'])

    if doc_id:
        if not cache_doc.retrieve_by_uuid(request.GET['index'], doc_id):
            raise Http404
    elif request.GET.get('url'):
        if not cache_doc.retrieve_by_filter(request.GET['index'], warc_target_uri=request.GET['url']):
            return render(request, 'cache-redirect.html', {'uri': request.GET['url']})

    doc_meta = cache_doc.doc_meta()
    context['cache']['uuid'] = doc_meta.meta.id
    context['cache']['meta'] = doc_meta

    content_type = doc_meta.http_content_type
    if not content_type:
        content_type = 'text/html'

    if plaintext_mode:
        content_type = 'text/plain'
        body = cache_doc.main_content()
    else:
        body = cache_doc.html(post_process_html)

    if raw_mode:
        return HttpResponse(body, content_type, 200)

    return render(request, 'cache.html', context)
