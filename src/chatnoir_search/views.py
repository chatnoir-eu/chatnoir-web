from django.shortcuts import render


from .search import SimpleSearch


def index(request):
    if not request.GET.get('q'):
        return render(request, 'search_frontend/index.html')

    search = SimpleSearch()
    results = search.search(request.GET.get('q'), 'webis_warc_clueweb12_011')

    context = {
        'search_results': results
    }
    return render(request, 'search_frontend/search.html', context)
