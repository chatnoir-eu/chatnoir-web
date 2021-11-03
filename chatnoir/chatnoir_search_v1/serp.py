# Copyright 2021 Janek Bevendorff
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import math
from collections import defaultdict

from elasticsearch_dsl.response import Response


# noinspection PyPep8Naming
class serp_api_meta(property):
    """
    Property indicating a basic response metadata property.
    """
    pass


# noinspection PyPep8Naming
class serp_api_meta_extra(property):
    """
    Property indicating an extended response metadata property.
    """
    pass


# noinspection PyPep8Naming
class api_value:
    """
    API response value wrapper.
    """
    def __init__(self, value):
        self.value = value

    @property
    def type(self):
        return type(self.value)

    def __repr__(self):
        return repr(self.value)

    def __str__(self):
        return str(self.value)


# noinspection PyPep8Naming
class minimal(api_value):
    """
    Minimal API response value wrapper.
    """
    pass


# noinspection PyPep8Naming
class extended(api_value):
    """
    Extended API response value wrapper.
    """
    pass


# noinspection PyPep8Naming
class explanation(extended):
    """
    Explanation field API response value wrapper.
    """
    pass


class SerpContext:
    """
    Results page context with processed results.
    """

    def __init__(self, query_string: str, search, response: Response):
        """
        :param query_string: original query string
        :param search: SimpleSearch object
        :param response: Elasticsearch DSL response
        """
        self._query_string = query_string
        self.search = search
        self.response = response

    def to_dict(self, hits=True, meta=True, meta_extra=False):
        """
        Return a single dict representation of this SERP context.

        :param hits: include (filtered) hit list
        :param meta: include basic meta data
        :param meta_extra: include extended meta data (implies ``meta=True``)
        :return: dict representation
        """
        d = {}
        if meta or meta_extra:
            d['meta'] = self.meta
        if meta_extra:
            d['meta'].update(self.meta_extra)
        if hits:
            d['hits'] = self.hits_filtered

        return d

    # noinspection DuplicatedCode
    @property
    def hits(self):
        """
        List of search result hits.

        Entries in this list contain all available fields, independent of the current search mode,
        hence it should not be used as an API response. Use :attr:`hits_filtered` instead.
        """

        results = []
        for hit in self.response.hits:
            body_key = 'body_lang.' + self.search.search_language
            meta_desc_key = 'meta_desc_lang.' + self.search.search_language

            snippet = self.search.get_snippet(hit, [body_key, meta_desc_key], 200)

            title_key = 'title_lang.' + self.search.search_language
            title = self.search.get_snippet(hit, [title_key], 60)
            if not title:
                title = '[ no title available ]'

            result_index = self._index_name_to_shorthand(hit.meta.index)
            target_uri = hit.warc_target_uri

            if result_index == 'cw09':
                # ClueWeb09 has buggy encoding, only thing we can do is strip <?> replacement characters
                title = title.replace('\ufffd', '')
                snippet = snippet.replace('\ufffd', '')
                target_uri = target_uri.replace('\ufffd', '')

            expl = None
            if hasattr(hit.meta, 'explanation'):
                expl = hit.meta.explanation.to_dict()

            result = {
                'score': minimal(hit.meta.score),
                'uuid': minimal(hit.meta.id),
                'index': minimal(result_index),
                'target_uri': minimal(target_uri),
                'target_hostname': extended(getattr(hit, 'warc_target_hostname', None)),
                'trec_id': extended(getattr(hit, 'warc_trec_id', None)),
                'page_rank': extended(getattr(hit, 'page_rank', None)),
                'spam_rank': extended(getattr(hit, 'spam_rank', None)),
                'title': minimal(title),
                'snippet': minimal(snippet),
                'explanation': explanation(expl)
            }

            results.append(result)

        if self.search.group_results_by_hostname:
            return self.group_results(results)

        return results

    @property
    def hits_filtered(self):
        """
        Key-filtered search results hit.

        The list is stripped of internal fields or fields not compatible with the current search mode,
        so it is suitable to be used directly in API responses.
        """
        hits = self.hits
        types = {minimal}
        if not self.search.minimal_response:
            types.add(extended)
        if self.search.explain:
            types.add(explanation)

        for i in range(len(hits)):
            hits[i] = {k: v.value for k, v in hits[i].items() if type(v) in types}

        return hits

    @property
    def meta(self):
        """
        JSON-serializable object of basic search result meta data.
        """
        return {k: getattr(self, k) for k in dir(self) if isinstance(getattr(type(self), k, None), serp_api_meta)}

    @property
    def meta_extra(self):
        """
        JSON-serializable object of extended search result meta data.
        """
        return {k: getattr(self, k) for k in dir(self) if isinstance(getattr(type(self), k, None), serp_api_meta_extra)}

    def _index_name_to_shorthand(self, index_name):
        """
        Inversely resolve internal index name to defined shorthand name.

        :param index_name: internal index name
        :return: shorthand or unmodified index name if not found
        """
        for i, v in self.search.selected_indices.items():
            if v['index'] == index_name:
                return i
        return index_name

    @staticmethod
    def group_results(results):
        """
         Group (bucket) results by host name, but preserve ranking order of first
         element in a group as well as the order within a group.

        :param results: ungrouped ordered search results
        """
        buckets = defaultdict(list)
        for result in results:
            suggest_grouping = True

            # First element in group
            if result['target_hostname'] not in buckets:
                suggest_grouping = False

            result['is_grouping_suggested'] = suggest_grouping
            buckets[result['target_hostname']].append(result)

        grouped_results = []
        for b in buckets:
            if len(buckets[b]) > 1:
                # Suggest "more from this host" for last result in a bucket
                buckets[b][-1]['is_more_suggested'] = True
            grouped_results.extend(buckets[b])

        return grouped_results

    @serp_api_meta
    def query_time(self):
        return self.response.took

    @serp_api_meta
    def total_results(self):
        return self.response.hits.total.value

    @serp_api_meta
    def indices(self):
        return list(self.search.selected_indices.keys())

    @serp_api_meta_extra
    def indices_all(self):
        all_indices = self.search.allowed_indices
        selected_indices = self.search.selected_indices
        return [dict(id=k, name=v.get('display_name'), selected=k in selected_indices)
                for k, v in all_indices.items()]

    @serp_api_meta_extra
    def query_string(self):
        """
        Original search query string.
        """
        return self._query_string

    @serp_api_meta_extra
    def current_page(self):
        """
        Current page number.
        """
        return min(self.search.page_num + 1, self.max_page)

    @serp_api_meta_extra
    def pagination_size(self):
        """
        Number of hits per page.
        """
        return 10

    @serp_api_meta_extra
    def results_from(self):
        """Index number of the first result."""
        return self.search.search_from

    @serp_api_meta_extra
    def results_to(self):
        """Index number of the last result."""
        return self.results_from + len(self.response.hits)

    @serp_api_meta_extra
    def max_page(self):
        """
        Maximum page number for pagination (respects general pagination limit).
        """
        return min(math.ceil(self.total_results / self.pagination_size), int(math.ceil(10000 / self.search.num_results)))

    @serp_api_meta_extra
    def explain(self):
        """
        Whether to explain results.
        """
        return self.search.explain

    @serp_api_meta_extra
    def terminated_early(self):
        return hasattr(self.response, 'terminated_early') and self.response.terminated_early
