from django.shortcuts import HttpResponse, render

from .cache import BasicHtmlFormatter, CacheDocument
from .search import SimpleSearchV1


def index(request):
    if not request.GET.get('q'):
        return render(request, 'search_frontend/index.html')

    query_string = request.GET.get('q')

    page_num = request.GET.get('p', '0')
    if page_num is None or not page_num.isnumeric():
        page_num = '0'
    page_num = max(0, int(page_num) - 1)

    indexes = request.GET.getlist('index')

    search = SimpleSearchV1(indexes, search_from=page_num * 10, num_results=10)
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
            'is_raw_mode': raw_mode,
            'search_query': request.GET.get('q', ''),
            'search_page': request.GET.get('p', '')
        }
    }

    cache_doc = CacheDocument()
    doc = None
    if request.GET.get('uuid'):
        doc = cache_doc.retrieve_by_uuid(request.GET['index'], request.GET['uuid'])
    elif request.GET.get('trec-id'):
        doc = cache_doc.retrieve_by_filter(request.GET['index'], warc_trec_id=request.GET['trec-id'])
    elif request.GET.get('url'):
        doc = cache_doc.retrieve_by_filter(request.GET['index'], warc_target_uri=request.GET['url'])
        if not doc:
            return render(request, 'search_frontend/cache-redirect.html', {'uri': request.GET['url']})

    if not doc:
        return render(request, '404.html', status=404)

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

    return render(request, 'search_frontend/cache.html', context)
