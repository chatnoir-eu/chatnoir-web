import os
import uuid

from django.core.cache import cache as django_cache
from django.conf import settings
from django.http import Http404, HttpResponseBadRequest, JsonResponse
from django.middleware.csrf import get_token
from django.shortcuts import HttpResponse, render
from django.utils.translation import gettext as _
from django.views.decorators.http import require_http_methods, require_safe
import frontmatter
import mistune

from .cache import BasicHtmlFormatter, CacheDocument
from .middleware import time_limited_csrf
from chatnoir_api_v1.search import SimpleSearch
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

    page_num = request.GET.get('p', '0')
    if page_num is None or not page_num.isnumeric():
        page_num = '0'
    page_num = max(0, int(page_num) - 1)

    indexes = request.GET.getlist('index')

    search = SimpleSearch(indexes, search_from=page_num * 10, num_results=10,
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

    cache_doc = CacheDocument(post_process_html)
    doc = None
    doc_id = request.GET.get('uuid')
    if not doc_id and request.GET.get('trec-id'):
        # Retrieve by internal document ID, which is usually faster than searching for the warc_trec_id term
        doc_id = webis_uuid(settings.SEARCH_INDICES[request.GET['index']]['warc_uuid_prefix'], request.GET['trec-id'])

    if doc_id:
        doc = cache_doc.retrieve_by_uuid(request.GET['index'], doc_id)
    elif request.GET.get('url'):
        doc = cache_doc.retrieve_by_filter(request.GET['index'], warc_target_uri=request.GET['url'])
        if not doc:
            return render(request, 'cache-redirect.html', {'uri': request.GET['url']})

    if not doc:
        raise Http404

    context['cache']['uuid'] = doc['meta'].meta.id
    context['cache']['meta'] = doc['meta']

    content_type = doc['meta'].http_content_type
    if not content_type:
        content_type = 'text/html'

    if plaintext_mode:
        doc['body'] = BasicHtmlFormatter.format(doc['body'])
        content_type = 'text/html'

    if raw_mode:
        return HttpResponse(doc['body'], content_type, 200)

    return render(request, 'cache.html', context)


def doc(request, subpath=''):
    subpath = subpath.strip('/')
    basedir = os.path.realpath(os.path.join(os.path.dirname(__file__), 'doc'))
    doc_path = os.path.realpath(os.path.join(basedir, subpath))

    if os.path.commonpath((basedir, doc_path)) != basedir:
        raise Http404

    if os.path.isdir(doc_path):
        doc_path = os.path.join(doc_path, 'index')

    doc_path += '.md'
    if not os.path.isfile(doc_path):
        raise Http404

    cache_key = '.'.join((__name__, 'doc', subpath))
    context = django_cache.get(cache_key)
    if context:
        return render(request, 'doc.html', context)

    source_doc = frontmatter.load(doc_path)
    rendered = mistune.html(source_doc.content)
    metadata = source_doc.metadata

    breadcrumbs = [dict(path='', title=_('ChatNoir Documentation'))]
    subpath_split = subpath.split('/')
    if 'breadcrumbs' in metadata:
        for p, t in zip(subpath_split, metadata['breadcrumbs']):
            breadcrumbs.append(dict(path=p, title=t))
    breadcrumbs.append(dict(path=subpath_split[-1], title=metadata.get('title', '')))

    metadata['breadcrumbs'] = breadcrumbs
    context = {
        'is_index': subpath in ('', 'index'),
        'meta': metadata,
        'doc_content': rendered
    }
    django_cache.set(cache_key, context, timeout=settings.DOC_PAGE_CACHE_TIMEOUT)
    return render(request, 'doc.html', context)
