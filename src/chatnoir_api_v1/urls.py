from django.urls import include, path
from rest_framework import routers

from . import views

app_name = 'api_v1'

router_v1 = routers.DefaultRouter(trailing_slash=False)
router_v1.APIRootView = views.APIRoot
router_v1.register(r'_search', views.SimpleSearchViewSet, basename='v1-search')
router_v1.register(r'_phrases', views.PhraseSearchViewSet, basename='v1-phrases')
router_v1.register(r'_manage_keys', views.ManageKeysInfoViewSet, basename='v1-manage-keys')

urlpatterns = [
    path(r'', include(router_v1.urls))
]
