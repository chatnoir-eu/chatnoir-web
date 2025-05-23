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
import re
from urllib import parse
import uuid

from django.conf import settings
from django.http import Http404, HttpResponseRedirect, HttpResponse, JsonResponse
from django.shortcuts import render
from django.utils.encoding import iri_to_uri
from django.views.decorators.http import require_safe

from chatnoir_search.elastic_backend import get_index
from elasticsearch_dsl import connections, Search
from .cache import CacheDocument


def bool_param_set(param_name, param_dict):
    return param_name in param_dict and param_dict[param_name] not in [None, '0', 'false', 'False']


def robots_txt(request):
    """Disallow all crawlers."""
    return HttpResponse('User-agent: *\nDisallow: /\n',
                        content_type=f'text/plain; charset={settings.DEFAULT_CHARSET}', status=200)


_URLSAFE_B64_UUID_REGEX = re.compile(r'^[a-zA-Z0-9_-]{22}$')
_CLUEWEB_TREC_ID_REGEX = re.compile(r'^clueweb[0-9]{2}-[a-z0-9-]{6}-[0-9]{2}-[0-9]{5}$')
_MS_MARCO_TREC_ID_REGEX = re.compile(r'^msmarco_.*$')
_LEGACY_UUID_REGEX = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$')


def normalize_doc_id_str(doc_id):
    """
    Validate and normalize a document UUID or ClueWeb ID string or MS MARCO ID or LongEval ID string.

    Valid Base64 UUIDs, ClueWeb IDs, and MS MARCO Ids will be passed through as-is.
    Legacy UUID hex strings will be converted to truncated and URL-safe Base64 if necessary.

    :raises ValueError: if ID has an invalid format
    """
    if doc_id:
        if len(doc_id) == 22 and _URLSAFE_B64_UUID_REGEX.match(doc_id):
            return doc_id
        if len(doc_id) == 25 and _CLUEWEB_TREC_ID_REGEX.match(doc_id):
            return doc_id
        if _MS_MARCO_TREC_ID_REGEX.match(doc_id):
            return doc_id
        if len(doc_id) == 36 and _LEGACY_UUID_REGEX.match(doc_id):
            # Convert hex encoding to URL-safe base64 and truncate '==' padding.
            # Underlying function will throw ValueError on error.
            return base64.urlsafe_b64encode(uuid.UUID(doc_id).bytes)[:-2].decode()
        try:
            # valid LongEval ID
            return str(int(doc_id))
        except:
            pass
    raise ValueError('Not a valid document ID.')


# noinspection PyProtectedMember
@require_safe
def cache(request):
    """Cache view."""
    index_shorthand = request.GET.get('index')
    search_index = get_index(index_shorthand)
    if not search_index:
        raise Http404

    raw_mode = bool_param_set('raw', request.GET)
    plain_mode = bool_param_set('plain', request.GET) and not raw_mode
    minimal_mode = bool_param_set('minimal', request.GET) and not plain_mode

    cache_doc = CacheDocument()
    found = False
    try:
        if request.GET.get('uuid'):
            found = cache_doc.retrieve_by_filter(search_index, uuid=normalize_doc_id_str(request.GET['uuid']))
        elif request.GET.get('trec-id'):
            found = cache_doc.retrieve_by_filter(
                search_index, warc_trec_id=normalize_doc_id_str(request.GET['trec-id']))
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
                    'uri': request.GET['url'],
                })
    except ValueError:
        pass

    if not found:
        raise Http404

    doc_meta = cache_doc.doc_meta()
    doc_uuid = doc_meta['uuid']
    cache_url = parse.urlparse(settings.CACHE_FRONTEND_URL)._replace(
        query=f'index={parse.quote(index_shorthand)}&uuid={parse.quote(doc_uuid)}')
    context = dict(
        app_name=settings.APPLICATION_NAME,
        search_frontend_url=settings.SEARCH_FRONTEND_URL,
        cache=dict(
            meta=doc_meta,
            title=cache_doc.html_title(),
            crawl_date=getattr(doc_meta, 'http_date', None) or getattr(doc_meta, 'warc_date', None),
            index=search_index.display_name,
            html_meta_viewport=cache_doc.html_meta_viewport(),
            cache_url=parse.urlunparse(cache_url),
            is_text_doc=cache_doc.is_text(),
            is_html_doc=cache_doc.is_html(),
            is_html_fragment_doc=cache_doc.is_html_fragment(),
            is_json_doc=cache_doc.is_json(),
            is_xml_doc=cache_doc.is_xml(),
            is_binary_doc=cache_doc.is_binary(),
        )
    )

    body = None
    if raw_mode or cache_doc.is_text() or cache_doc.is_binary():
        body = cache_doc.bytes()
    elif not cache_doc.is_binary() and (
            plain_mode or minimal_mode or cache_doc.is_html_fragment() or cache_doc.is_xml()):
        body = cache_doc.main_content(
            minimal_html=((cache_doc.is_html() and minimal_mode) or cache_doc.is_html_fragment()) and not plain_mode)
    elif cache_doc.is_html():
        body = cache_doc.html(not raw_mode)

    if cache_doc.is_text() and raw_mode:
        content_type = f'text/plain; charset={settings.DEFAULT_CHARSET}'
    elif not raw_mode:
        content_type = 'text/html; charset=utf-8'
    else:
        content_type = iri_to_uri(cache_doc.raw_doc_content_type())
        charset = doc_meta.content_encoding or settings.DEFAULT_CHARSET
        content_type = f'{content_type}; charset={charset}'

    if raw_mode:
        response = HttpResponse(body, content_type=content_type, status=200)
    else:
        if not cache_doc.is_binary():
            body_key = 'html' if (cache_doc.is_html() and not minimal_mode) else 'plainhtml'
            if cache_doc.is_text() or plain_mode:
                body_key = 'plaintext'
            context['cache'][f'body_{body_key}'] = body
        response = render(request, 'cache.html', context=context, content_type=content_type)

    response['X-Robots-Tag'] = 'noindex,nofollow'
    response['Link'] = f'<{iri_to_uri(doc_meta.warc_target_uri)}>; rel="canonical"'
    return response


@require_safe
def term_vectors(request):
    """Get term vector for a document, useful for query expansion, relevance feedback, etc."""

    if 'default' not in connections.connections._conns:
        connections.configure(default=settings.ELASTICSEARCH_PROPERTIES)

    index_shorthand = request.GET.get('index')
    search_index = get_index(index_shorthand)
    if not search_index:
        raise Http404

    if 'trec-id' not in request.GET:
        raise Http404

    results = Search().index(search_index).filter('term', warc_trec_id=request.GET.get('trec-id')).execute()
    if not results.hits or len(results.hits) < 1:
        raise Http404

    results = list(set([i.meta['id'] for i in results.hits]))

    if len(results) != 1:
        raise Http404

    es_id = results[0]

    ret = connections.get_connection().termvectors(index=search_index.index._name, id=es_id, term_statistics=True, field_statistics=False, fields=['body_lang_en'])
    assert ret['_id'] == es_id
    
    return JsonResponse(ret, status=200)
