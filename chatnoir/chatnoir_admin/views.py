from django.conf import settings
from django.contrib import admin
from django.shortcuts import render
from elasticsearch_dsl import connections
from elasticsearch.helpers import bulk

from chatnoir_search.elastic_backend import get_index
from web_cache.cache import CacheDocument
from .forms import TakedownForm


def takedowns(request):
    form = TakedownForm(request.POST or None)

    taken_down = []
    takedown_undone = []
    not_found = []

    if request.method == 'POST' and form.is_valid():
        takedown_ids = form.cleaned_data['urls']

        if 'default' not in connections.connections._conns:
            connections.configure(default=settings.ELASTICSEARCH_PROPERTIES)

        indices = {}
        es = connections.get_connection()
        index_refresh_pending = set()
        bulk_actions = []
        for u, t in takedown_ids.items():
            if t['index'] not in indices:
                i = get_index('cw22')
                if not i:
                    not_found.append(u)
                    continue
                indices[t['index']] = get_index(t['index'])
            index = indices[t['index']]
            doc = CacheDocument()
            if not doc.retrieve_by_filter(index, uuid=t['uuid']):
                not_found.append(u)
                continue
            doc_meta = doc.doc_meta()
            bulk_actions.append({
                '_op_type': 'update',
                '_index': doc_meta.meta.index,
                '_id': doc_meta.meta.id,
                'doc': {'takedown': t['takedown']},
            })
            index_refresh_pending.add(doc_meta.meta.index)

            if t['takedown']:
                taken_down.append(u)
            else:
                takedown_undone.append(u)

        if bulk_actions:
            bulk(es, bulk_actions)
        if index_refresh_pending:
            es.indices.refresh(index=list(index_refresh_pending))

    context = {
        **admin.site.each_context(request),
        'form': form,
        'taken_down': taken_down,
        'takedown_undone': takedown_undone,
        'not_found': not_found,
    }
    return render(request, 'admin/takedowns.html', context)
