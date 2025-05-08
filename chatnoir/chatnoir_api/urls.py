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

from django.urls import include, path, reverse_lazy
from django.views.generic import RedirectView
from rest_framework import routers

from . import views

app_name = 'chatnoir_api'

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
router_v1.register(r'.+', views.Error404, basename='v1-error-404')


urlpatterns = [
    path(r'api/', RedirectView.as_view(url=reverse_lazy('chatnoir_api:api-root'))),
    path(r'api/v1/', include(router_v1.urls)),
]
