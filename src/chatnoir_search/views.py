from django.shortcuts import HttpResponse, render

from .cache import CacheDocument
from .search import SimpleSearchV1


def index(request):
    if not request.GET.get('q'):
        return render(request, 'search_frontend/index.html')

    query_string = request.GET.get('q')

    page_num = request.GET.get('p', '0')
    if page_num is None or not page_num.isnumeric():
        page_num = '0'
    page_num = max(0, int(page_num) - 1)

    indices = request.GET.getlist('index')

    search = SimpleSearchV1(indices, page_num)
    serp_context = search.search(query_string)

    context = {
        'search_query': query_string,
        'serp_context': serp_context,
        'search_results': serp_context.results
    }
    return render(request, 'search_frontend/search.html', context)


def cache(request):
    if 'index' not in request.GET:
        return render(request, '404.html', status=404)

    raw_mode = 'raw' in request.GET
    plaintext_mode = 'plain' in request.GET
    context = {
        'cache': {
            'index': request.GET.get('index'),
            'is_plaintext_mode': plaintext_mode,
            'is_raw_mode': raw_mode
        }
    }

    cache_doc = CacheDocument()
    doc = None
    if request.GET.get('uuid'):
        doc = cache_doc.retrieve_by_uuid(request.GET['index'], request.GET['uuid'], plaintext_mode)
    elif request.GET.get('uri'):
        doc = cache_doc.retrieve_by_filter(request.GET['index'], plaintext_mode, warc_target_uri=request.GET['uri'])
    elif request.GET.get('trec-id'):
        doc = cache_doc.retrieve_by_filter(request.GET['index'], plaintext_mode, warc_trec_id=request.GET['trec-id'])

    if not doc:
        return render(request, '404.html', status=404)

    context['cache']['uuid'] = doc['meta'].meta.id
    context['cache']['uri'] = doc['meta'].warc_target_uri

    if raw_mode:
        return HttpResponse(doc['body'], doc['meta'].content_type, 200)

    return render(request, 'search_frontend/cache.html', context)
