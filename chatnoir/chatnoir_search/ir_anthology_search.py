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

from chatnoir_search import search as chatnoir_search
from chatnoir_search.ir_anthology_serp import SerpContext
from chatnoir_search.types import FieldName

# Monkey-patch ChatNoir SerpContext
chatnoir_search.SerpContext = SerpContext

_field_pattern = '{field}_lang.{lang}'


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
        'index': FieldName('#index', False),
        'lang': FieldName('lang', False),
        'doi': FieldName('doi', False),
        'author': FieldName('authors', False),
        'year<>': FieldName('year', False),
        'venue': FieldName('venue', False)
    }

    """Default search fields."""
    MAIN_FIELDS = [
        {
            'name': FieldName('title', pattern=_field_pattern),
            'boost': 80,
            'proximity_matching': True,
            'proximity_slop': 2,
            'proximity_boost': 30
        },
        {
            'name': FieldName('abstract', pattern=_field_pattern),
            'boost': 60,
            'proximity_matching': True,
            'proximity_slop': 2,
            'proximity_boost': 20
        },
        {
            'name': FieldName('full_text', pattern=_field_pattern),
            'boost': 20,
            'proximity_matching': True,
            'proximity_slop': 2,
            'proximity_boost': 20
        },
        {
            'name': FieldName('authors', False),
            'boost': 50
        },
        {
            'name': FieldName('venue', False),
            'boost': 30
        },
        {
            'name': FieldName('doi', False),
            'boost': 100
        }
    ]

    HIGHLIGHT_FIELDS = [
        {
            'name': FieldName('title', pattern=_field_pattern),
            'fragment_size': 70,
            'number_of_fragments': 1
        },
        {
            'name': FieldName('abstract', pattern=_field_pattern),
            'fragment_size': 300,
            'number_of_fragments': 1
        },
        {
            'name': FieldName('full_text', pattern=_field_pattern),
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
            'name': FieldName('full_text', pattern=_field_pattern),
            'boost': 1.0
        },
        {
            'name': FieldName('abstract', pattern=_field_pattern),
            'boost': 2.0
        }
    ]

    """Terminate search after this many results per node."""
    NODE_LIMIT = 4000
