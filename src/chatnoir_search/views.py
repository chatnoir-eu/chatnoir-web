from django.shortcuts import render


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
