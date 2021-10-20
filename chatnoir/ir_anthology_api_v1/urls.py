from ir_anthology_api_v1.search import PhraseSearch, SimpleSearch
from chatnoir_api_v1.urls import *
import chatnoir_api_v1.views as views

app_name = 'ir_anthology_api_v1'

views.SimpleSearch = SimpleSearch
views.PhraseSearch = PhraseSearch
