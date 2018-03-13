from django.http import HttpResponseRedirect
from django.shortcuts import render

from .forms import KeyRequestForm


def index(request):
    context = {}
    return render(request, 'frontend/index.html', context)


def request_key(request):
    if request.method == 'POST':
        form = KeyRequestForm(request.POST)

        if form.is_valid():
            return HttpResponseRedirect('/request_sent')
        else:
            return render(request, 'frontend/index.html', {'form': form})
    else:
        form = KeyRequestForm()

    return render(request, 'frontend/index.html', {'form': form})
