from django.conf import settings
from django.shortcuts import render


from .search import SimpleSearchV1


def index(request):
    if not request.GET.get('q'):
        return render(request, 'search_frontend/index.html')

    search = SimpleSearchV1('webis_warc_commoncrawl15_002')
    query_string = request.GET.get('q')

    results_page_num = request.GET.get('p', '0')
    page_size = settings.SERP_RESULTS_PER_PAGE
    if results_page_num is None or not results_page_num.isnumeric():
        results_page_num = '0'
    results_page_num = max(0, int(results_page_num) - 1)
    results_from = results_page_num * page_size

    serp_context = search.search(query_string, results_from, page_size)

    context = {
        'search_query': query_string,
        'serp_context': serp_context,
        'search_results': serp_context.results
    }
    return render(request, 'search_frontend/search.html', context)
