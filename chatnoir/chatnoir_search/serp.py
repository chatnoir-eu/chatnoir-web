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
from urllib import parse

from django.utils.translation import gettext as _
from django.urls import reverse
from elasticsearch_dsl.response import Response

from chatnoir_search.types import *


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

    def to_dict(self, hits=True, meta=True, extended_meta=False):
        """
        Return a single dict representation of this SERP context.

        :param hits: include (filtered) hit list
        :param meta: include basic metadata
        :param extended_meta: include extended metadata (implies ``meta=True``)
        :return: dict representation
        """
        d = {}
        if meta or extended_meta:
            d['meta'] = self.meta
        if extended_meta:
            d['meta'].update(self.meta_extended)
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
            lang = getattr(hit, 'lang', self.search.search_language)

            body_field = FieldName('body')
            meta_desc_field = FieldName('meta_desc')
            snippet = self.search.get_snippet(hit, [body_field.i18n(lang), meta_desc_field.i18n(lang)], 200)

            title_field = FieldName('title')
            title = self.search.get_snippet(hit, [title_field.i18n(lang)], 60)
            if not title:
                title = _('[ no title available ]')

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

            doc_id = getattr(hit, 'uuid', hit.meta.id)
            result = {
                'index': minimal(result_index),
                'uuid': minimal(doc_id),
                'warc_id': extended(hit.warc_record_id),
                'trec_id': extended(getattr(hit, 'warc_trec_id', None)),
                'score': minimal(hit.meta.score),
                'external_uri': minimal(target_uri),
                'internal_uri': minimal(reverse('chatnoir_web:cache') + '?index={}&uuid={}'.format(
                    parse.quote(result_index), parse.quote(doc_id))),
                'target_hostname': extended(getattr(hit, 'warc_target_hostname', None)),
                'page_rank': extended(getattr(hit, 'page_rank', None)),
                'spam_rank': extended(getattr(hit, 'spam_rank', None)),
                'title': minimal(title),
                'snippet': minimal(snippet),
                'content_type': extended(getattr(hit, 'content_type', None)),
                'lang': extended(getattr(hit, 'lang', None)),
                'date': extended(getattr(hit, 'date', None)),
                'explanation': explanation(expl)
            }

            results.append(result)

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
        JSON-serializable object of basic search result metadata.
        """
        return {k: getattr(self, k) for k in dir(self) if isinstance(getattr(type(self), k, None), serp_api_meta)}

    @property
    def meta_extended(self):
        """
        JSON-serializable object of extended search result metadata.

        Trailing underscores are stripped from all included property names, so this can be used for
        overwriting fields with the same name (except the underscore) from the simple metadata set.
        """
        return {k.rstrip('_'): getattr(self, k) for k in dir(self)
                if isinstance(getattr(type(self), k, None), serp_api_meta_extended)}

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

    @serp_api_meta
    def query_time(self):
        """Query time in milliseconds."""
        return self.response.took

    @serp_api_meta
    def total_results(self):
        """Total hits found for the query."""
        return self.response.hits.total.value

    @serp_api_meta
    def indices(self):
        """List of searched index IDs."""
        return list(self.search.selected_indices.keys())

    @serp_api_meta_extended
    def indices_(self):
        """List of dicts with index IDs and names and whether they were active for this search."""
        all_indices = self.search.allowed_indices
        selected_indices = self.search.selected_indices
        return [dict(id=k, name=v.get('display_name'), selected=k in selected_indices)
                for k, v in all_indices.items()]

    @serp_api_meta_extended
    def query_string(self):
        """
        Original search query string.
        """
        return self._query_string

    @serp_api_meta_extended
    def results_from(self):
        """Index number of the first result."""
        return self.search.search_from

    @serp_api_meta_extended
    def results_to(self):
        """Index number past the last returned result."""
        return self.results_from + len(self.response.hits)

    @serp_api_meta_extended
    def page_size(self):
        """
        Maximum number of results per page for paginated result display.
        This can be larger than ``hits_returned``, which is the actual number of results on this page.
        """
        return self.search.num_results

    @serp_api_meta_extended
    def max_page(self):
        """
        Maximum page number for pagination (respects general pagination limit).
        """
        return min(math.ceil(self.total_results / self.page_size), int(math.ceil(10000 / self.search.num_results)))

    @serp_api_meta_extended
    def explain(self):
        """
        Whether to explain results.
        """
        return self.search.explain

    @serp_api_meta_extended
    def terminated_early(self):
        return hasattr(self.response, 'terminated_early') and self.response.terminated_early
