from django.conf import settings
from django.contrib import admin
from django.shortcuts import render
from elasticsearch_dsl import Q, Search, connections
from elasticsearch.helpers import bulk

from chatnoir_search.elastic_backend import get_index
from .forms import TakedownForm


def takedowns(request):
    form = TakedownForm(request.POST or None)

    result = False
    taken_down_uuid = []
    takedown_undone_uuid = []
    taken_down_prefix = []
    takedown_undone_prefix = []
    not_found_uuid = set()
    not_found_prefix = set()

    if request.method == 'POST' and form.is_valid():
        takedown_ids = form.cleaned_data['urls']
        not_found_uuid.update((v['index'], v['uuid']) for v in takedown_ids.values())
        takedown_prefixes = form.cleaned_data['warc_target_uri_prefixes']
        not_found_prefix.update(takedown_prefixes.keys())

        if 'default' not in connections.connections._conns:
            connections.configure(default=settings.ELASTICSEARCH_PROPERTIES)

        index_refresh_pending = set()
        bulk_actions = {}

        # Collect exact-UUID takedowns from cache URLs first
        takedowns_by_index = {}
        indices = {}
        for u, t in takedown_ids.items():
            if t['index'] not in indices:
                i = get_index('cw22')
                if not i:
                    continue
                indices[t['index']] = get_index(t['index'])
            takedowns_by_index.setdefault(t['index'], []).append((u, t))

        uuid_takedowns_by_index = {}
        for index_name, requests_for_index in takedowns_by_index.items():
            uuid_takedowns_by_index[index_name] = {
                t['uuid']: (u, t['takedown']) for u, t in requests_for_index
            }

        # Build all-index exact-UUID and warc_target_uri search actions for warc_target_uri prefixes
        matched_exact_uuids = {index_name: set() for index_name in uuid_takedowns_by_index}
        matched_prefix_stats = {
            prefix: {'count': 0, 'indices': set()} for prefix in takedown_prefixes
        }
        for index_name in settings.SEARCH_INDICES:
            if not takedown_prefixes and index_name not in uuid_takedowns_by_index:
                continue

            search_index = get_index(index_name)
            if not search_index:
                continue

            # Combine UUID terms and prefix queries into should clauses
            should_queries = []
            exact_actions = uuid_takedowns_by_index.get(index_name, {})
            if exact_actions:
                should_queries.append(Q('terms', uuid=list(exact_actions.keys())))
            for prefix, do_take_down in takedown_prefixes.items():
                should_queries.append(Q('prefix', warc_target_uri=do_take_down['prefix']))

            if not should_queries:
                continue

            # Concatenate individual should queries
            query = should_queries[0]
            for subquery in should_queries[1:]:
                query |= subquery

            # Search warc meta index for existing UUIDs / prefixes
            search = (Search()
                      .index(search_index.warc_index_name)
                      .query(query)
                      .source(['uuid', 'warc_target_uri']))
            for hit in search.scan():
                do_take_down = None
                if index_name in uuid_takedowns_by_index and hit.uuid in uuid_takedowns_by_index[index_name]:
                    url, takedown = uuid_takedowns_by_index[index_name][hit.uuid]
                    matched_exact_uuids[index_name].add(hit.uuid)
                    not_found_uuid.discard((index_name, hit.uuid))
                    do_take_down = takedown
                    if takedown:
                        taken_down_uuid.append(url)
                    else:
                        takedown_undone_uuid.append(url)

                for prefix, prefix_action in takedown_prefixes.items():
                    if getattr(hit, 'warc_target_uri', '').startswith(prefix_action['prefix']):
                        matched_prefix_stats[prefix]['count'] += 1
                        matched_prefix_stats[prefix]['indices'].add(hit.meta.index)
                        do_take_down = prefix_action['takedown']
                        not_found_prefix.discard(prefix)

                if do_take_down is None:
                    continue

                # Build update bulk actions
                bulk_actions[(hit.meta.index, hit.meta.id)] = {
                    '_op_type': 'update',
                    '_index': hit.meta.index,
                    '_id': hit.meta.id,
                    'doc': {'takedown': do_take_down},
                }
                index_refresh_pending.add(hit.meta.index)

        # Summarise prefix takedown stats
        for prefix, action in takedown_prefixes.items():
            count = matched_prefix_stats[prefix]['count']
            index_count = len(matched_prefix_stats[prefix]['indices'])
            prefix_result = {'prefix': prefix, 'count': count, 'index_count': index_count}
            if action['takedown']:
                taken_down_prefix.append(prefix_result)
            else:
                takedown_undone_prefix.append(prefix_result)

        result = True

        es = connections.get_connection()
        if bulk_actions:
            bulk(es, bulk_actions.values())

        if index_refresh_pending:
            es.indices.refresh(index=list(index_refresh_pending))

    context = {
        **admin.site.each_context(request),
        'form': form,
        'result': result,
        'taken_down_uuid': taken_down_uuid,
        'takedown_undone_uuid': takedown_undone_uuid,
        'not_found_uuid': not_found_uuid,
        'taken_down_prefix': taken_down_prefix,
        'takedown_undone_prefix': takedown_undone_prefix,
        'not_found_prefix': not_found_prefix,
    }
    return render(request, 'admin/takedowns.html', context)
