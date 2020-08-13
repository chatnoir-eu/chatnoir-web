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
    context = {
        'cache': {
            'uuid': request.GET.get('uuid', ''),
            'index': request.GET.get('index', ''),
            'is_plaintext_mode': 'plain' in request.GET
        }
    }

    if 'raw' in request.GET:
        doc = CacheDocument().retrieve_by_uuid(request.GET.get('uuid'), request.GET.get('index'))
        if doc is None:
            return render(request, '404.html', status=404)

        return HttpResponse(doc['body'], doc['meta'].content_type, 200)

    return render(request, 'search_frontend/cache.html', context)
