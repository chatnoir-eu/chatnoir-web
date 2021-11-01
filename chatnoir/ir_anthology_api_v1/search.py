from urllib.parse import quote_plus
import uuid

from chatnoir_api_v1 import search as search_v1
from chatnoir_api_v1.search import minimal, extended, explanation


class SimpleSearch(search_v1.SimpleSearch):
    """
    Simple search (version 1).
    """

    """
    Available user query filters.
    
    Assumes string matching by default. Add "<>" to the name to enable numeric range queries (e.g. "year<>").
    #index is a special placeholder value for user-selected index names.
    """
    QUERY_FILTERS = {
        'index': '#index',
        'lang': 'lang',
        'doi': 'doi',
        'author': 'authors',
        'year<>': 'year',
        'venue': 'venue'
    }

    """Default search fields."""
    MAIN_FIELDS = [
        {
            'name': 'title_lang.%lang%',
            'boost': 80,
            'proximity_matching': True,
            'proximity_slop': 2,
            'proximity_boost': 30
        },
        {
            'name': 'abstract_lang.%lang%',
            'boost': 60,
            'proximity_matching': True,
            'proximity_slop': 2,
            'proximity_boost': 20
        },
        {
            'name': 'full_text_lang.%lang%',
            'boost': 20,
            'proximity_matching': True,
            'proximity_slop': 2,
            'proximity_boost': 20
        },
        {
            'name': 'authors',
            'boost': 50
        },
        {
            'name': 'venue',
            'boost': 30
        },
        {
            'name': 'doi',
            'boost': 100
        }
    ]

    HIGHLIGHT_FIELDS = [
        {
            'name': 'title_lang.%lang%',
            'fragment_size': 70,
            'number_of_fragments': 1
        },
        {
            'name': 'abstract_lang.%lang%',
            'fragment_size': 300,
            'number_of_fragments': 1
        },
        {
            'name': 'full_text_lang.%lang%',
            'fragment_size': 300,
            'number_of_fragments': 1
        }
    ]

    """Numeric query filters."""
    RANGE_FILTERS = []

    """Additional fields for boosting queries."""
    BOOSTS = []

    """Terminate search after this many results per node."""
    NODE_LIMIT = 70000

    """Number of top documents to rescore."""
    RESCORE_WINDOW = 1000


class PhraseSearch(search_v1.PhraseSearch):
    """Default for how far terms can be apart in a phrase."""
    DEFAULT_SLOP = 0

    """Maximum allowed phrase slop."""
    MAX_SLOP = 2

    """Fields to search."""
    MAIN_FIELDS = [
        {
            'name': 'full_text_lang.%lang%',
            'boost': 1.0
        },
        {
            'name': 'abstract_lang.%lang%',
            'boost': 2.0
        }
    ]

    """Terminate search after this many results per node."""
    NODE_LIMIT = 4000


# noinspection DuplicatedCode
class SerpContext(search_v1.SerpContext):
    @property
    def hits(self):
        """
        Result list from the given hits list.
        """

        results = []
        for hit in self.response.hits:
            full_text_key = 'full_text_lang.' + self.search.search_language
            abstract_key = 'abstract_lang.' + self.search.search_language

            snippet = self.search.get_snippet(hit, [full_text_key, abstract_key], 200)

            title_key = 'title_lang.' + self.search.search_language
            title = self.search.get_snippet(hit, [title_key], 60)
            if not title:
                title = '[ no title available ]'

            result_index = self._index_name_to_shorthand(hit.meta.index)

            expl = None
            if hasattr(hit.meta, 'explanation'):
                expl = hit.meta.explanation.to_dict()

            result = {
                'score': minimal(hit.meta.score),
                'index': minimal(result_index),
                'uuid': minimal(uuid.uuid5(uuid.NAMESPACE_URL, 'ir-anthology:' + hit.meta.id)),
                'internal_uri': minimal(f'https://ir.webis.de/anthology/{quote_plus(hit.meta.id)}/'),
                'external_uri': minimal(f'https://doi.org/{getattr(hit, "doi")}' if hasattr(hit, 'doi') else None),
                'authors': extended(list(getattr(hit, 'authors', []))),
                'doi': minimal(getattr(hit, 'doi', None)),
                'anthology_id': minimal(hit.meta.id),
                'venue': extended(getattr(hit, 'venue', None)),
                'year': extended(getattr(hit, 'year', None)),
                'title': minimal(title),
                'snippet': extended(snippet),
                'explanation': explanation(expl)
            }

            results.append(result)

        return results


search_v1.SerpContext = SerpContext
