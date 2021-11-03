from chatnoir_search_v1 import ir_anthology_search
from chatnoir_api_v1.urls import *
import chatnoir_api_v1.views as views

app_name = 'ir_anthology_api_v1'

# Monkey-patch search backends
views.SimpleSearch = ir_anthology_search.SimpleSearch
views.PhraseSearch = ir_anthology_search.PhraseSearch
