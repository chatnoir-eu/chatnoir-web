from sigir21_chatonir_api_v1.search import PhraseSearch, SimpleSearch

import chatnoir_web.views as views
from chatnoir_web.views import index

views.SimpleSearch = SimpleSearch
views.PhraseSearch = PhraseSearch
