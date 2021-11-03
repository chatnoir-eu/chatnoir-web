from chatnoir_search_v1 import ir_anthology_search

import chatnoir_web.views as views
from chatnoir_web.views import index, search

# Monkey-patch search backends
views.SimpleSearch = ir_anthology_search.SimpleSearch
views.PhraseSearch = ir_anthology_search.PhraseSearch
