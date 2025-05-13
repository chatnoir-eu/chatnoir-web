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

import re
from abc import ABC, abstractmethod
import locale
import logging

from django.conf import settings
from elasticsearch_dsl import Q, Search, connections

from chatnoir_search.serp import SerpContext
from chatnoir_search.types import FieldName, FieldValue


class SearchBase(ABC):
    """
    Simple search base class.
    """

    SEARCH_VERSION = None

    def __init__(self, indices=None, search_from=0, num_results=10, explain=False):
        """
        :param indices: list of indices to search (will be validated and replaced with defaults if necessary)
        :param search_from: start search at this result index
        :param num_results: number of results to return
        :param explain: explain result scores
        """
        if indices is not None and type(indices) not in (list, tuple, set):
            raise TypeError('indices must be a list')

        if indices is None:
            indices = {settings.SEARCH_DEFAULT_INDICES[self.SEARCH_VERSION]}
        self._indices_unvalidated = set(indices)

        self.search_language = 'en'
        self.num_results = max(1, num_results)
        self.search_from = max(0, min(search_from, 10000 - self.num_results))
        self.explain = explain
        self.minimal_response = False

        self.query_logger = logging.getLogger(f'query_log.{self.__class__.__name__}')
        self.query_logger.setLevel(logging.INFO)

        if 'default' not in connections.connections._conns:
            connections.configure(default=settings.ELASTICSEARCH_PROPERTIES)

    @property
    def allowed_indices(self):
        """Allowed and compatible indices."""
        indices = {k: settings.SEARCH_INDICES[k] for k in settings.SEARCH_INDICES
                   if self.SEARCH_VERSION in settings.SEARCH_INDICES[k]['compat_search_versions']}
        if not indices:
            raise RuntimeError('No indices configured for selected search version.')
        return indices

    @property
    def selected_indices(self):
        """Selected indices."""
        allowed = self.allowed_indices
        indices = {k: allowed[k] for k in self._indices_unvalidated if k in allowed}
        if not indices:
            indices = {k: v for k, v in allowed.items() if v.get('default')}

        if not indices:
            raise RuntimeError('No default index configured,')

        return indices

    @property
    def default_search_method(self, default='default'):
        """The search method used by default for an index."""
        conf = list(self.selected_indices.values())
        if len(conf) <= 0:
            return default

        return conf[0].get('default_search_method', default)

    @property
    def pre_query_flags(self, default='AND|OR|NOT|WHITESPACE'):
        """Query flags for retrieval in the pre-query stage."""
        conf = list(self.selected_indices.values())
        if len(conf) <= 0:
            return default

        return conf[0].get('pre_query_flags', default)

    @property
    def rescore_query_flags(self, default='AND|OR|NOT|PHRASE|PREFIX|PRECEDENCE|WHITESPACE'):
        """Query flags for retrieval in the rescore-query stage."""
        conf = list(self.selected_indices.values())
        if len(conf) <= 0:
            return default

        return conf[0].get('rescore_query_flags', default)

    def log_query(self, query, extra):
        """
        Log a search query using the configured query logging facility.
        Calls to :meth:``search`` are not logged automatically, so it is the responsibility of
        the user to call :meth:``log_query`` as needed.

        :param query: the search query as a string
        :param extra: extra arguments to pass to the logger as dict
        """
        self.query_logger.log(logging.INFO, "%s", query, extra=extra)

    @abstractmethod
    def search(self, query):
        """
        Run a search based on given search fields.

        :param query: search query as string
        :return: :class:``serp.SerpContext`` with result
        """
        pass

    def get_snippet(self, hit, fields, max_len):
        """
        Extract snippet from hit.

        :param hit: hit to extract from
        :param fields: list of fields to try for snippets in order
        :param max_len: maximum length of a snippet if not extracted from a highlight
        """
        snippet = ''
        for field in fields:
            if hasattr(hit.meta, 'highlight') and hasattr(hit.meta.highlight, field):
                fragments = getattr(hit.meta.highlight, field)
                if fragments and fragments[0]:
                    return fragments[0].strip()

            if hasattr(hit, field):
                snippet = getattr(hit, field)
                if len(snippet) > max_len:
                    snippet = snippet[:max_len]
                    # Get rid of incomplete words
                    if snippet[-1].isspace():
                        return snippet.strip()
                    pos = snippet.rfind(' ')
                    if pos != -1:
                        # Shorten snippet if it doesn't become too short then
                        if .6 * max_len <= pos:
                            return snippet[:pos].strip()

            return snippet.strip()


class SimpleSearch(SearchBase):
    """
    Simple search (version 1).
    """

    SEARCH_VERSION = 1

    """
    Available retrieval model implementation.
    """
    SEARCH_METHODS = ['default', 'bm25']

    """
    Available user query filters.
    
    Assumes string matching by default. Add "<>" to the name to enable numeric range queries (e.g. "year<>").
    #index is a special placeholder value for user-selected index names.
    """
    QUERY_FILTERS = {
        'site': FieldName('warc_target_hostname.raw', False),
        'lang': FieldName('lang', False),
        'index': FieldName('#index', False)
    }

    """Default search fields."""
    MAIN_FIELDS = [
        {
            'name': FieldName('title'),
            'boost': 70,
            'proximity_matching': True,
            'proximity_slop': 2,
            'proximity_boost': 30
        },
        {
            'name': FieldName('body'),
            'boost': 10,
            'proximity_matching': True,
            'proximity_slop': 2,
            'proximity_boost': 20
        },
        {
            'name': FieldName('full_body')
        },
        {
            'name': FieldName('headings'),
            'boost': 5
        },
        {
            'name': FieldName('meta_desc'),
            'boost': 1
        },
        {
            'name': FieldName('meta_keywords'),
            'boost': 1
        },
        {
            'name': FieldName('warc_target_hostname', False),
            'boost': 1
        },
        {
            'name': FieldName('warc_target_path', False),
            'boost': 10
        },
        {
            'name': FieldName('warc_target_hostname.raw', False),
            'fuzzy_matching': True,
            'boost': 10
        }
    ]

    """Highlight fields for snippets"""
    HIGHLIGHT_FIELDS = [
        {
            'name': FieldName('title'),
            'fragment_size': 70,
            'number_of_fragments': 1
        },
        {
            'name': FieldName('body'),
            'fragment_size': 300,
            'number_of_fragments': 1
        }
    ]

    """Numeric query filters."""
    RANGE_FILTERS = [
        {
            'name': FieldName('body_length', False),
            'gte': 100
        },
        {
            'name': FieldName('spam_rank', False),
            'gte': 66,
            'include_unset': True
        }
    ]

    """Additional fields for boosting queries."""
    BOOSTS = [
        {
            'name': FieldName('warc_target_hostname.raw', False),
            'value': FieldValue(r'{lang}\.wikipedia\.org', True),
            'match': True,
            'boost': 30,
            'match_boost': 50
        },
        {
            'name': FieldName('warc_target_path.raw', False),
            'value': FieldValue(r'/(wiki/|index\\.[a-z]+)?'),
            'match': False,
            'boost': 70
        }
    ]

    """Terminate search after this many results per node."""
    NODE_LIMIT = 70000

    """Number of top documents to rescore."""
    RESCORE_WINDOW = 400

    def __init__(self, indices=None, search_from=0, num_results=10, explain=False, search_method='default'):
        super().__init__(indices, search_from, num_results, explain)
        if search_method not in self.SEARCH_METHODS:
            raise ValueError(f'Invalid search method "{search_method}"')
        self.search_method = search_method
        if not self.search_method:
            self.search_method = self.default_search_method

    def search(self, query):
        search_implementation = getattr(self, f'_build_{self.search_method}_search_request')
        response = search_implementation(query).execute()
        return SerpContext(query, self, response)

    def _build_default_search_request(self, query):
        """
        Build search request including pre-query, rescorer, node limit, highlighters etc.

        :param query: user query as string
        :return: configured Search
        """

        # Parse query string and apply side effects
        query, user_filters = self._parse_query_string_operators(query)

        pre_query = self._build_pre_query(query)
        pre_query.filter.extend(user_filters.filter)
        pre_query.must_not.extend(user_filters.must_not)

        s = (Search()
             .index([i['index'] for i in self.selected_indices.values()])
             .query(pre_query)
             .extra(from_=self.search_from,
                    size=self.num_results,
                    terminate_after=self.NODE_LIMIT,
                    track_total_hits=True,
                    explain=self.explain)
             .highlight_options(encoder='html'))

        for h in self.HIGHLIGHT_FIELDS:
            s = s.highlight(h['name'].i18n(self.search_language), **{k: v for k, v in h.items() if k != 'name'})

        rescore_query = self._build_rescore_query(query)
        if rescore_query is not None:
            s = s.extra(rescore=dict(
                window_size=self.RESCORE_WINDOW,
                query=dict(
                    query_weight=0.01,
                    rescore_query_weight=0.99,
                    score_mode='total',
                    rescore_query=rescore_query.to_dict()
                )
            ))

        return s

    def _build_bm25_search_request(self, query):
        """
        Build search request that uses an Anserini-inspired retrieval approach of doing BM25 on the default text.

        :param query: user query as string
        :return: configured Search
        """
        s = (Search()
             .index([i['index'] for i in self.selected_indices.values()])
             .query("multi_match", query=query, fields=[f"body_lang_{self.search_language}"])
             .extra(from_=self.search_from,
                    size=self.num_results,
                    terminate_after=self.NODE_LIMIT,
                    track_total_hits=True,
                    explain=self.explain)
             .highlight_options(encoder='html'))

        for h in self.HIGHLIGHT_FIELDS:
            s = s.highlight(h['name'].i18n(self.search_language), **{k: v for k, v in h.items() if k != 'name'})

        return s

    def _parse_query_string_operators(self, query):
        """
        Parse (non-standard) operators and configured filters from the query string such as site:example.com and
        delete the filters from the given query StringBuffer.

        :param query: user query as string
        :return: stripped query string, generated filter query
        """

        query = re.sub(r'(?!\B"[^"]*) AND (?![^"]*"\B)', ' +', query)
        query = re.sub(r'(?!\B"[^"]*) OR (?![^"]*"\B)', ' | ', query)
        query_string_orig = query

        filter_query = Q('bool', filter=[])

        for filter_keyword in self.QUERY_FILTERS:
            filter_field = self.QUERY_FILTERS[filter_keyword].i18n(self.search_language)

            is_range = filter_keyword.endswith('<>')
            value_match = r'("[^"]+"|[^"]\S*)' if not is_range else r'(\d+)'
            filter_keyword = filter_keyword.strip('<>')
            kw_esc = re.escape(filter_keyword)

            for filter_match in re.finditer(
                    rf'(?:^|(?<=\s))({kw_esc})([<>]=?|[=:])\s*{value_match}(?:$|\s)',
                    query_string_orig):
                filter_value = filter_match.group(3).strip()

                if is_range and not filter_value.isdigit():
                    continue

                # Remove filter from query string
                query = query.replace(query_string_orig[filter_match.start():filter_match.end()], '', 1)

                # Special case: index
                if filter_field == '#index':
                    self._indices_unvalidated = [i.strip() for i in filter_value.split(',')]
                    continue

                # Special case: language
                if filter_field == 'lang':
                    if filter_value in locale.locale_alias:
                        self.search_language = filter_value
                    continue

                if is_range and filter_match.group(2) in ('<', '<=', '>', '>='):
                    filter_query.filter.append(
                        Q('range', **{filter_field: {
                            ('lte' if filter_match.group(2).startswith('<') else 'gte'): filter_value}
                        }))
                else:
                    query_type = 'match_phrase' if ' ' in filter_value else 'match'
                    filter_query.filter.append(Q(query_type, **{
                        filter_field.i18n(self.search_language): filter_value.strip('"')}))

            query_string_orig = query.strip()

        query = query.strip()
        return query, filter_query

    def _build_pre_query(self, query):
        """
        Assemble the fast pre-query for use with a rescorer.

        :param query: user query string
        :return: assembled pre-query
        """

        pre_query = Q('bool', filter=[], must_not=[])
        pre_query.filter.append(Q('term', lang=self.search_language))
        if query:
            pre_query.must = Q('simple_query_string',
                               query=query,
                               default_operator='and',
                               flags=self.pre_query_flags,
                               fields=[f['name'].i18n(self.search_language) for f in self.MAIN_FIELDS])
        else:
            pre_query.must = Q('match_all')

        range_filters = self._build_range_filters()
        pre_query.filter.extend(range_filters.filter)
        pre_query.must_not.extend(range_filters.must_not)

        pre_query.should.extend(self._build_boost_query(True).should)

        return pre_query

    def _build_rescore_query(self, query_string):
        proximity_fields = []
        fuzzy_fields = []
        simple_query = Q('simple_query_string',
                         query=query_string,
                         minimum_should_match='30%',
                         flags=self.rescore_query_flags,
                         fields=[])

        rescore_query = Q('bool', must=simple_query, should=[])

        for f in self.MAIN_FIELDS:
            simple_query.fields.append(f'{f["name"].i18n(self.search_language)}^{f.get("boost", 1.0)}')

            if f.get('proximity_matching', False):
                proximity_fields.append((
                    f['name'].i18n(self.search_language),
                    f.get('proximity_slop', 1),
                    f.get('proximity_boost', 1.0) / 2.0
                ))

            if f.get('fuzzy_matching', False):
                fuzzy_fields.append(f['name'])

        for pf in proximity_fields:
            rescore_query.should.append(
                Q('match_phrase', **{pf[0]: {'query': query_string, 'slop': pf[1], 'boost': pf[2]}})
            )

        for ff in fuzzy_fields:
            rescore_query.should.append(
                Q('fuzzy', **{ff: {'value': query_string, 'fuzziness': 'AUTO'}})
            )

        rescore_query.should.extend(self._build_boost_query(False).should)
        return rescore_query

    def _build_range_filters(self):
        """
        Build numeric filter queries from config to the given query.
        """
        bool_query = Q('bool', filter=[], must_not=[])
        for f in self.RANGE_FILTERS:
            field_name = f['name'].i18n(self.search_language)
            filter_query = Q('range', **{field_name: {k: v for k, v in f.items() if k in ['gt', 'gte', 'lt', 'lte']}})
            if f.get('include_unset', False):
                must_not_exist_query = Q('bool', must_not=Q('exists', field=field_name))
                filter_query = Q('bool', should=[filter_query, must_not_exist_query])

            if f.get('negate', False):
                bool_query.must_not.append(filter_query)
            else:
                bool_query.filter.append(filter_query)

        return bool_query

    def _build_boost_query(self, match):
        """
        Add (positive) boosts from config to the given query.

        :param match: only add boosts which are allowed during match phase (pre-query)
        """
        boost_query = Q('bool', should=[])
        for b in self.BOOSTS:
            if match and not b.get('match', False):
                continue

            regexp_query = Q('regexp', **{
                b['name'].i18n(self.search_language): {
                    'value': b['value'].i18n(self.search_language),
                    'boost': b.get('match_boost', 1.0) if match else b.get('boost', 1.0)
                }
            })
            boost_query.should.append(regexp_query)
        return boost_query


class PhraseSearch(SimpleSearch):
    """Default for how far terms can be apart in a phrase."""
    DEFAULT_SLOP = 0

    """Maximum allowed phrase slop."""
    MAX_SLOP = 2

    """Fields to search."""
    MAIN_FIELDS = [
        {
            'name': FieldName('body'),
            'boost': 1.0
        }
    ]

    """Terminate search after this many results per node."""
    NODE_LIMIT = 4000

    def __init__(self, indices=None, search_from=0, num_results=10, explain=False, slop=None):
        super().__init__(indices, search_from, num_results, explain)
        self.slop = slop or self.DEFAULT_SLOP

    def _build_pre_query(self, query):
        pre_query = Q('bool', filter=[], must_not=[])
        pre_query.filter.append(Q('term', lang=self.search_language))

        pre_query.must = []
        main_fields = set()
        for f in self.MAIN_FIELDS:
            fname = f['name'].i18n(self.search_language)
            main_fields.add(fname)
            pre_query.must.append(Q('match_phrase', **{fname: dict(
                query=query,
                slop=min(self.slop, self.MAX_SLOP),
                boost=f.get('boost', 1.0))}))

        pre_query.should = []
        for f in super().MAIN_FIELDS:
            fname = f['name'].i18n(self.search_language)
            if fname in main_fields:
                continue
            pre_query.should.append(Q('match', **{fname: dict(query=query, boost=f.get('boost', 1.0))}))

        return pre_query

    def _build_rescore_query(self, query_string):
        return None
