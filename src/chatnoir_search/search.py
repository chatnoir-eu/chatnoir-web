from django.conf import settings

from elasticsearch import Elasticsearch
from elasticsearch_dsl import Q, Search
from elasticsearch_dsl.search import Response

from abc import ABC
from collections import defaultdict
import re
from urllib.parse import urlparse


class SimpleSearch(ABC):
    """
    Simple search base class.
    """
    CLIENT = Elasticsearch(settings.ELASTICSEARCH_HOSTS)

    def __init__(self, indices):
        """
        :param indices: list of indices to search
        """
        self.indices = indices
        self.search_language = 'en'
        self.group_results_by_hostname = True

    def search(self, query_string, results_from, results_size):
        """
        Run a search based on given search fields.

        :param query_string: search query
        :param results_from: first result to return
        :param results_size: number of results to return
        """
        pass

    def locale_fieldname(self, field_name):
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


class SimpleSearchV1(SimpleSearch):
    """
    Simple search (version 1).
    """

    """Available user query filters."""
    QUERY_FILTERS = {
        'site': 'warc_target_hostname.raw',
        'lang': 'lang',
        'index': '#index'
    }

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

    RESCORE_WINDOW = 400

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

    def __init__(self, indices):
        super().__init__(indices)
        self.user_lang_override = False

    def search(self, query_string, results_from, results_size):
        results_from = min(results_from, 10000)
        results_size = results_size if results_from + results_size <= 10000 else 0
        response = self.build_search_request(query_string, results_from, results_size).execute()
        return SerpContext(self, response, results_from, results_size)

    def build_search_request(self, query_string, results_from, results_size):
        """
        Build search request including pre-query, rescorer, node limit, highlighters etc.

        :param query_string: user query string
        :param results_from: first result to return
        :param results_size: number of results to return
        :return: configured SearchRequestBuilder
        """
        s = Search() \
            .using(SimpleSearch.CLIENT) \
            .index(self.indices) \
            .query(self.build_pre_query(query_string)) \
            .extra(rescore={
                'window_size': SimpleSearchV1.RESCORE_WINDOW,
                'query': {
                    'query_weight': 0.0,
                    'rescore_query_weight': 1.0,
                    'score_mode': 'total',
                    'rescore_query': self.build_rescore_query(query_string).to_dict()
                }
            }, terminate_after=70000) \
            .highlight('title_lang.' + self.search_language, fragment_size=70, number_of_fragments=1) \
            .highlight('body_lang.' + self.search_language, fragment_size=300, number_of_fragments=1) \
            .highlight_options(encoder='html')

        return s[results_from:results_size]

    def build_pre_query(self, query_string):
        """
        Assemble the fast pre-query for use with a rescorer.

        :param query_string: user query string
        :return: assembled pre-query
        """

        query_string, pre_query = self.parse_query_string_operators(query_string)
        if not self.user_lang_override:
            # Only add if not already added via user filter
            pre_query.filter.append(Q('term', lang=self.search_language))

        if query_string:
            pre_query.must = Q('simple_query_string',
                               query=query_string,
                               default_operator='and',
                               flags='AND|OR|NOT|WHITESPACE',
                               fields=[self.locale_fieldname(f['name']) for f in SimpleSearchV1.MAIN_FIELDS])
        else:
            pre_query.must = Q('match_all')

        range_filters = self.build_range_filters()
        pre_query.filter.extend(range_filters.filter)
        pre_query.must_not.extend(range_filters.must_not)

        pre_query.should.extend(self.build_boost_query(True).should)

        return pre_query

    def build_rescore_query(self, query_string):
        proximity_fields = []
        fuzzy_fields = []

        simple_query = Q('simple_query_string',
                         query=query_string,
                         minimum_should_match='30%',
                         flags='AND|OR|NOT|PHRASE|PREFIX|WHITESPACE',
                         fields=[])

        rescore_query = Q('bool', must=simple_query, should=[])

        for f in SimpleSearchV1.MAIN_FIELDS:
            simple_query.fields.append(f'{self.locale_fieldname(f["name"])}^{f.get("boost", 1.0)}')

            if f.get('proximity_matching', False):
                proximity_fields.append((
                    self.locale_fieldname(f['name']),
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

        rescore_query.should.extend(self.build_boost_query(False).should)
        return rescore_query

    def parse_query_string_operators(self, query_string):
        """
        Parse (non-standard) operators and configured filters from the query string such as site:example.com and
        delete the filters from the given query StringBuffer.

        :param query_string: user query string
        :return: stripped query string, generated filter query
        """

        query_string = re.sub(r'(?!\B"[^"]*) AND (?![^"]*"\B)', ' +', query_string)
        query_string = re.sub(r'(?!\B"[^"]*) OR (?![^"]*"\B)', ' | ', query_string)

        filter_query = Q('bool', filter=[])
        for filter_keyword in SimpleSearchV1.QUERY_FILTERS:

            filter_match = re.search(r'(?:^|\s)({}):\s*((\S+)(?:$|\s))'.format(re.escape(filter_keyword)), query_string)
            if not filter_match:
                continue

            # Remove filter from query string
            query_string = query_string[:filter_match.start(1)] + query_string[filter_match.end(2):]
            filter_value = filter_match.group(3)

            # Build filter term
            filter_field = SimpleSearchV1.QUERY_FILTERS[filter_keyword]

            # Special case: index
            if filter_field == '#index':
                self.indices = [i.strip() for i in filter_value.split(',')]
                continue

            # Special case: hostname
            if filter_field == 'warc_target_hostname.raw':
                self.group_results_by_hostname = False

            # Special case: language
            if filter_field == 'lang':
                self.search_language = filter_value
                self.user_lang_override = True

            filter_query.filter.append(Q('term', **{filter_field: filter_value}))

        query_string = query_string.strip()
        return query_string, filter_query

    def build_range_filters(self):
        """
        Build numeric filter queries from config to the given query.
        """
        bool_query = Q('bool', filter=[], must_not=[])
        for f in SimpleSearchV1.RANGE_FILTERS:
            field_name = self.locale_fieldname(f['name'])
            filter_query = Q('range', **{field_name: {k: v for k, v in f.items() if k in ['gt', 'gte', 'lt', 'lte']}})
            if f.get('include_unset', False):
                must_not_exist_query = Q('bool', must_not=Q('exists', field=field_name))
                filter_query = Q('bool', should=[filter_query, must_not_exist_query])

            if f.get('negate', False):
                bool_query.must_not.append(filter_query)
            else:
                bool_query.filter.append(filter_query)

        return bool_query

    def build_boost_query(self, match):
        """
        Add (positive) boosts from config to the given query.

        :param match: only add boosts which are allowed during match phase (pre-query)
        """
        boost_query = Q('bool', should=[])
        for b in SimpleSearchV1.BOOSTS:
            if match and not b.get('match', False):
                continue

            regexp_query = Q('regexp', **{
                self.locale_fieldname(b['name']): {
                    'value': self.locale_fieldname(b['value']),
                    'boost': b.get('match_boost', 1.0) if match else b.get('boost', 1.0)
                }
            })
            boost_query.should.append(regexp_query)
        return boost_query


class SerpContext:
    """
    Results page context with processed results.
    """

    def __init__(self, search: SimpleSearch, response: Response, results_from, results_size):
        self.search = search
        self.response = response
        self.hits = response.hits
        self.results_from = results_from
        self.results_size = results_size

    @property
    def results(self):
        """
        Result list from the given hits list.
        """

        results = []
        for hit in self.hits:
            body_key = 'body_lang.' + self.search.search_language
            meta_desc_key = 'meta_desc_lang.' + self.search.search_language

            snippet = self.search.get_snippet(hit, [body_key, meta_desc_key], 200)

            title_key = 'title_lang.' + self.search.search_language
            title = self.search.get_snippet(hit, [title_key], 60)
            if not title:
                title = '[ no title available ]'

            result = {
                'score': hit.meta.score,
                'index': hit.meta.index,
                'document_id': hit.meta.id,
                'trec_id': getattr(hit, 'warc_trec_id', None),
                'title': title,
                'target_hostname': hit.warc_target_hostname,
                'target_path': urlparse(hit.warc_target_uri).path,
                'target_uri': hit.warc_target_uri,
                'snippet': snippet,
                'page_rank': getattr(hit, 'page_rank', None),
                'spam_rank': getattr(hit, 'spam_rank', None)
            }

            results.append(result)

        if self.search.group_results_by_hostname:
            return self.group_results(results)

        return results

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

    @property
    def results_to(self):
        """Index number of the last result."""
        return self.results_from + self.results_size

    @property
    def total_results(self):
        return self.hits.total

    @property
    def terminated_early(self):
        return hasattr(self.response, 'terminated_early') and self.response.terminated_early

    @property
    def query_time(self):
        return self.response.took
