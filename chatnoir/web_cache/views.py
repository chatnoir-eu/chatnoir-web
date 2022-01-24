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
from django.http import Http404, HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_safe

from .cache import CacheDocument


def bool_param_set(param_name, param_dict):
    return param_name in param_dict and param_dict[param_name] not in [None, '0', 'false', 'False']


def webis_uuid(prefix, doc_id):
    """
    Calculate Webis UUID from a corpus prefix and a document ID.
    """
    return str(uuid.uuid5(uuid.NAMESPACE_URL, ':'.join((prefix, doc_id))))


@require_safe
def index(request):
    if 'index' not in request.GET or request.GET.get('index') not in settings.SEARCH_INDICES:
        raise Http404

    raw_mode = bool_param_set('raw', request.GET)
    plaintext_mode = bool_param_set('plain', request.GET)
    post_process_html = not bool_param_set('no-rewrite', request.GET)
    context = dict(
        app_name=settings.APPLICATION_NAME,
        cache_frontend_url=settings.CACHE_FRONTEND_URL,
        cache=dict(
            index=request.GET.get('index'),
            is_plaintext_mode=plaintext_mode,
            is_raw_mode=raw_mode,
            search_query=request.GET.get('q', ''),
            search_page=request.GET.get('p', '')
        )
    )

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
    context['cache'].update(dict(
        uuid=doc_meta.meta.id,
        meta=doc_meta,
        title=cache_doc.html_title()
    ))

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
