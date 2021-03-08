from sigir21_chatonir_api_v1.search import SimpleSearch

import chatnoir_web.views
from chatnoir_web.views import index

chatnoir_web.views.SimpleSearch = SimpleSearch
