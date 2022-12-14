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

import base64
import uuid

from django.conf import settings
from django.http import Http404, HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.utils.encoding import iri_to_uri
from django.views.decorators.http import require_safe

from chatnoir_search.elastic_backend import get_index
from .cache import CacheDocument


def bool_param_set(param_name, param_dict):
    return param_name in param_dict and param_dict[param_name] not in [None, '0', 'false', 'False']


def robots_txt(request):
    """Disallow all crawlers."""
    return HttpResponse('User-agent: *\nDisallow: /\n',
                        content_type=f'text/plain; charset={settings.DEFAULT_CHARSET}', status=200)


def normalize_uuid_str(uuid_str):
    """Convert a legacy UUID hex string to truncated and URL-safe Base64 if necessary (or return it as is)."""
    if uuid_str and len(uuid_str) == 36 and '-' in uuid_str:
        try:
            # Convert hex encoding to URL-safe base64 and truncate '==' padding
            return base64.urlsafe_b64encode(uuid.UUID(uuid_str).bytes)[:-2].decode()
        except ValueError:
            pass

    return uuid_str


@require_safe
def cache(request):
    """Cache view."""

    search_index = get_index(request.GET.get('index'))
    if not search_index:
        raise Http404

    raw_mode = bool_param_set('raw', request.GET)
    plaintext_mode = bool_param_set('plain', request.GET)

    cache_doc = CacheDocument()
    found = False
    if request.GET.get('uuid'):
        found = cache_doc.retrieve_by_filter(search_index, uuid=normalize_uuid_str(request.GET['uuid']))
    elif request.GET.get('idx-uuid'):
        found = cache_doc.retrieve_by_idx_id(search_index, normalize_uuid_str(request.GET['idx-uuid']))
    elif request.GET.get('trec-id'):
        found = cache_doc.retrieve_by_filter(search_index, warc_trec_id=request.GET['trec-id'])
    elif request.GET.get('url'):
        if not request.GET['url'].startswith('https://') and not request.GET['url'].startswith('http://'):
            # Do not redirect to unsafe URLs
            raise Http404

        found = cache_doc.retrieve_by_filter(search_index, warc_target_uri=request.GET['url'])
        if not found:
            if raw_mode and request.META.get('HTTP_REFERER', '').startswith(settings.CACHE_FRONTEND_URL):
                # Don't show redirect page for directly embedded content
                return HttpResponseRedirect(request.GET['url'])

            return render(request, 'cache-redirect.html', {
                'app_name': settings.APPLICATION_NAME,
                'uri': request.GET['url']
            })

    if not found:
        raise Http404

    doc_meta = cache_doc.doc_meta()
    context = dict(
        app_name=settings.APPLICATION_NAME,
        cache_frontend_url=settings.CACHE_FRONTEND_URL,
        cache=dict(
            uuid=doc_meta.meta.id,
            meta=doc_meta,
            title=cache_doc.html_title(),
            index=search_index.display_name,
            index_shorthand=request.GET.get('index'),
            is_plaintext_mode=plaintext_mode or cache_doc.is_text_plain(),
            is_plaintext_doc=cache_doc.is_text_plain(),
            is_html_doc=cache_doc.is_html()
        )
    )

    if plaintext_mode or cache_doc.is_text_plain():
        body = cache_doc.main_content()
    elif cache_doc.is_html():
        body = cache_doc.html(not raw_mode)
    else:
        raw_mode = True
        body = cache_doc.bytes()

    content_type = iri_to_uri(doc_meta.http_content_type) if raw_mode else 'text/html'
    charset = doc_meta.content_encoding if raw_mode else settings.DEFAULT_CHARSET
    content_type = f'{content_type}; charset={charset}'

    if raw_mode:
        response = HttpResponse(body, content_type=content_type, status=200)
    else:
        context['cache']['body'] = body
        response = render(request, 'cache.html', context=context, content_type=content_type)

    response['X-Robots-Tag'] = 'noindex,nofollow'
    response['Link'] = f'<{iri_to_uri(doc_meta.warc_target_uri)}>; rel="canonical"'
    return response
