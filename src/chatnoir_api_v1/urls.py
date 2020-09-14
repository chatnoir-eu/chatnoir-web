from django.urls import include, path
from rest_framework import routers

from . import views

app_name = 'api_v1'

router_v1 = routers.DefaultRouter(trailing_slash=False)
router_v1.APIRootView = views.APIRoot
router_v1.register(r'_search', views.SimpleSearchViewSet, basename='v1-search')
router_v1.register(r'_phrases', views.PhraseSearchViewSet, basename='v1-phrases')
router_v1.register(r'_manage_keys', views.ManageKeysInfoViewSet, basename='v1-manage-keys')
router_v1.register(r'_manage_keys/create', views.ManageKeysCreateViewSet, basename='v1-manage-keys-create')
router_v1.register(r'_manage_keys/update/(?P<target_apikey>[^/]+)',
                   views.ManageKeysUpdateViewSet, basename='v1-manage-keys-update')
router_v1.register(r'_manage_keys/revoke/(?P<target_apikey>[^/]+)',
                   views.ManageKeysRevokeViewSet, basename='v1-manage-keys-revoke')

urlpatterns = [
    path(r'', include(router_v1.urls))
]
