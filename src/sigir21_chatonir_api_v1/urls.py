from sigir21_chatonir_api_v1.search import PhraseSearch, SimpleSearch
from chatnoir_api_v1.urls import *
import chatnoir_api_v1.views as views

views.SimpleSearch = SimpleSearch
views.PhraseSearch = PhraseSearch
