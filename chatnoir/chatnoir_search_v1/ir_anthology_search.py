from chatnoir_search_v1 import search as chatnoir_search
from chatnoir_search_v1.ir_anthology_serp import SerpContext

# Monkey-patch ChatNoir SerpContext
chatnoir_search.SerpContext = SerpContext


class SimpleSearch(chatnoir_search.SimpleSearch):
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


class PhraseSearch(chatnoir_search.PhraseSearch):
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
