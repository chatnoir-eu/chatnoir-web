import math
import re
from abc import ABC, abstractmethod
from collections import defaultdict, deque
from urllib.parse import urlparse

from django.conf import settings
from elasticsearch_dsl import Q, Search, connections
from elasticsearch_dsl.search import Response


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
        if indices is not None and type(indices) not in (tuple, list):
            raise TypeError('indices must be a list')

        if indices is None:
            indices = {settings.SEARCH_DEFAULT_INDICES[self.SEARCH_VERSION]}
        self._indices_unvalidated = set(indices)

        self.search_language = 'en'
        self.group_results_by_hostname = True
        self.num_results = max(1, num_results)
        self.search_from = max(0, min(search_from, 10000 - self.num_results))
        self.explain = explain
        self.minimal_response = False

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
    def page_num(self):
        """Search result page number."""
        return self.search_from // self.num_results

    @abstractmethod
    def search(self, query_string):
        """
        Run a search based on given search fields.

        :param query_string: search query
        """
        pass

    def replace_lang_placeholder(self, field_name):
        """
        Helper function to localize field names according to the current search language.

        :param field_name: field name with language placeholders
        :return: localized field name
        """
        return field_name.replace('%lang%', self.search_language)

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
    Available user query filters.
    
    Assumes string matching by default. Add "<>" to the name to enable numeric range queries (e.g. "year<>").
    #index is a special placeholder value for user-selected index names.
    """
    QUERY_FILTERS = {
        'site': 'warc_target_hostname.raw',
        'lang': 'lang',
        'index': '#index'
    }

    """Default search fields."""
    MAIN_FIELDS = [
        {
            'name': 'title_lang.%lang%',
            'boost': 70,
            'proximity_matching': True,
            'proximity_slop': 2,
            'proximity_boost': 30
        },
        {
            'name': 'body_lang.%lang%',
            'boost': 10,
            'proximity_matching': True,
            'proximity_slop': 2,
            'proximity_boost': 20
        },
        {
            'name': 'full_body_lang.%lang%'
        },
        {
            'name': 'headings_lang.%lang%',
            'boost': 5
        },
        {
            'name': 'meta_desc_lang.%lang%',
            'boost': 1
        },
        {
            'name': 'meta_keywords_lang.%lang%',
            'boost': 1
        },
        {
            'name': 'warc_target_hostname',
            'boost': 1
        },
        {
            'name': 'warc_target_path',
            'boost': 10
        },
        {
            'name': 'warc_target_hostname.raw',
            'fuzzy_matching': True,
            'boost': 10
        }
    ]

    """Highlight fields for snippets"""
    HIGHLIGHT_FIELDS = [
        {
            'name': 'title_lang.%lang%',
            'fragment_size': 70,
            'number_of_fragments': 1
        },
        {
            'name': 'body_lang.%lang%',
            'fragment_size': 300,
            'number_of_fragments': 1
        }
    ]

    """Numeric query filters."""
    RANGE_FILTERS = [
        {
            'name': 'body_length',
            'gte': 100
        },
        {
            'name': 'spam_rank',
            'gte': 66,
            'include_unset': True
        }
    ]

    """Additional fields for boosting queries."""
    BOOSTS = [
        {
            'name': 'warc_target_hostname.raw',
            'value': r'%lang%\.wikipedia\.org',
            'match': True,
            'boost': 30,
            'match_boost': 50
        },
        {
            'name': 'warc_target_path.raw',
            'value': r'/(wiki/|index\\.[a-z]+)?',
            'match': False,
            'boost': 70
        }
    ]

    """Terminate search after this many results per node."""
    NODE_LIMIT = 70000

    """Number of top documents to rescore."""
    RESCORE_WINDOW = 400

    def __init__(self, indices=None, search_from=0, num_results=10, explain=False):
        super().__init__(indices, search_from, num_results, explain)
        self.user_lang_override = False

    def search(self, query_string):
        response = self._build_search_request(query_string).execute()
        return SerpContext(query_string, self, response)

    def _build_search_request(self, query_string):
        """
        Build search request including pre-query, rescorer, node limit, highlighters etc.

        :param query_string: user query string
        :param explain: explain result ranking
        :return: configured Search
        """

        # Parse query string and apply side effects
        query_string, user_filters = self._parse_query_string_operators(query_string)

        pre_query = self._build_pre_query(query_string)
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
            s = s.highlight(self.replace_lang_placeholder(h['name']), **{k: v for k, v in h.items() if k != 'name'})

        rescore_query = self._build_rescore_query(query_string)
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

    def _parse_query_string_operators(self, query_string):
        """
        Parse (non-standard) operators and configured filters from the query string such as site:example.com and
        delete the filters from the given query StringBuffer.

        :param query_string: user query string
        :return: stripped query string, generated filter query
        """

        query_string = re.sub(r'(?!\B"[^"]*) AND (?![^"]*"\B)', ' +', query_string)
        query_string = re.sub(r'(?!\B"[^"]*) OR (?![^"]*"\B)', ' | ', query_string)
        query_string_orig = query_string

        filter_query = Q('bool', filter=[])

        for filter_keyword in self.QUERY_FILTERS:
            filter_field = self.QUERY_FILTERS[filter_keyword]

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
                query_string = query_string.replace(query_string_orig[filter_match.start():filter_match.end()], '', 1)

                # Special case: index
                if filter_field == '#index':
                    self._indices_unvalidated = [i.strip() for i in filter_value.split(',')]
                    continue

                # Special case: hostname
                if filter_field == 'warc_target_hostname.raw':
                    self.group_results_by_hostname = False

                # Special case: language
                if filter_field == 'lang':
                    self.search_language = filter_value
                    self.user_lang_override = True

                if is_range and filter_match.group(2) in ('<', '<=', '>', '>='):
                    filter_query.filter.append(
                        Q('range', **{filter_field: {
                            ('lte' if filter_match.group(2).startswith('<') else 'gte'): filter_value}
                        }))
                else:
                    query_type = 'match_phrase' if ' ' in filter_value else 'match'
                    filter_query.filter.append(Q(query_type, **{filter_field: filter_value.strip('"')}))

            query_string_orig = query_string.strip()

        query_string = query_string.strip()
        return query_string, filter_query

    def _build_pre_query(self, query_string):
        """
        Assemble the fast pre-query for use with a rescorer.

        :param query_string: user query string
        :return: assembled pre-query
        """

        pre_query = Q('bool', filter=[], must_not=[])

        if not self.user_lang_override:
            # Only add if not already added via user filter
            pre_query.filter.append(Q('term', lang=self.search_language))

        if query_string:
            pre_query.must = Q('simple_query_string',
                               query=query_string,
                               default_operator='and',
                               flags='AND|OR|NOT|WHITESPACE',
                               fields=[self.replace_lang_placeholder(f['name']) for f in self.MAIN_FIELDS])
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
                         flags='AND|OR|NOT|PHRASE|PREFIX|WHITESPACE',
                         fields=[])

        rescore_query = Q('bool', must=simple_query, should=[])

        for f in self.MAIN_FIELDS:
            simple_query.fields.append(f'{self.replace_lang_placeholder(f["name"])}^{f.get("boost", 1.0)}')

            if f.get('proximity_matching', False):
                proximity_fields.append((
                    self.replace_lang_placeholder(f['name']),
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
            field_name = self.replace_lang_placeholder(f['name'])
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
                self.replace_lang_placeholder(b['name']): {
                    'value': self.replace_lang_placeholder(b['value']),
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
            'name': 'body_lang.%lang%',
            'boost': 1.0
        }
    ]

    """Terminate search after this many results per node."""
    NODE_LIMIT = 4000

    def __init__(self, indices=None, search_from=0, num_results=10, explain=False, slop=None):
        super().__init__(indices, search_from, num_results, explain)
        self.slop = slop or self.DEFAULT_SLOP

    def _build_pre_query(self, query_string):
        pre_query = Q('bool', filter=[], must_not=[])

        if not self.user_lang_override:
            # Only add if not already added via user filter
            pre_query.filter.append(Q('term', lang=self.search_language))

        pre_query.must = []
        main_fields = set()
        for f in self.MAIN_FIELDS:
            fname = self.replace_lang_placeholder(f['name'])
            main_fields.add(fname)
            pre_query.must.append(Q('match_phrase', **{fname: dict(
                query=query_string,
                slop=min(self.slop, self.MAX_SLOP),
                boost=f.get('boost', 1.0))}))

        pre_query.should = []
        for f in super().MAIN_FIELDS:
            fname = self.replace_lang_placeholder(f['name'])
            if fname in main_fields:
                continue
            pre_query.should.append(Q('match', **{fname: dict(query=query_string, boost=f.get('boost', 1.0))}))

        return pre_query

    def _build_rescore_query(self, query_string):
        return None


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

    def __init__(self, query_string: str, search: SearchBase, response: Response):
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
        :param meta_extra: include extended meta data
        :return: dict representation
        """
        d = {}
        if meta:
            d['meta'] = self.meta
        if meta_extra:
            d['meta_extra'] = self.meta_extra
        if hits:
            d['hits'] = self.hits_filtered

        return d

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
        return self.results_from + self.results_size

    @serp_api_meta_extra
    def results_size(self):
        """Number of results returned on this page."""
        return len(self.response.hits)

    @serp_api_meta_extra
    def max_page(self):
        """
        Maximum allowed page number for pagination.
        """
        return int(math.ceil(10000 / self.search.num_results))

    @serp_api_meta_extra
    def explain(self):
        """
        Whether to explain results.
        """
        return self.search.explain

    @serp_api_meta_extra
    def terminated_early(self):
        return hasattr(self.response, 'terminated_early') and self.response.terminated_early

    @serp_api_meta_extra
    def pagination(self):
        current_page = min(self.search.page_num + 1, self.max_page)
        first_page = max(1, current_page - self.pagination_size // 2)
        last_page = min(self.max_page, current_page + (self.pagination_size - (current_page - first_page) - 1))
        last_page = min(last_page, math.ceil(self.total_results / self.search.num_results))
        pages = deque({'num': p, 'label': str(p)} for p in range(first_page, last_page + 1))

        if current_page > 1:
            pages.appendleft({'num': current_page - 1, 'label': '«', 'label_aria': 'Previous'})
        if first_page > 1:
            pages.appendleft({'num': 1, 'label': '←', 'label_aria': 'First'})
        if current_page < last_page:
            pages.append({'num': current_page + 1, 'label': '»', 'label_aria': 'Next'})

        return {
            'first_page': first_page,
            'last_page': last_page,
            'current_page': current_page,
            'pages': list(pages)
        }
