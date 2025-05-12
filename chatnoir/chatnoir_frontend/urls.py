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

from django.urls import path

from . import views

app_name = 'chatnoir_frontend'

urlpatterns = [
    path(r'', views.index, name='index'),

    # API key requests forms
    path(r'apikey/', views.index, name='apikey_request_index'),
    path(r'apikey/request-academic', views.apikey_request_academic, name='apikey_request_academic'),
    path(r'apikey/request-passcode', views.apikey_request_passcode, name='apikey_request_passcode'),
    path(r'apikey/request-received', views.index, name='request_received'),
    path(r'apikey/verify/', views.apikey_request_verify, name='apikey_request_verify_index'),
    path(r'apikey/verify/<slug:activation_code>', views.apikey_request_verify, name='apikey_request_verify'),

    # API Docs
    path(r'docs/', views.docs, name='docs_index'),
    path(r'docs/api-general', views.docs, name='docs_api_general'),
    path(r'docs/api-advanced', views.docs, name='docs_api_advanced'),
    path(r'docs/api-advanced/management', views.docs, name='docs_api_advanced_management'),

    # Cache redirect
    path(r'cache', views.cache, name='cache'),
]
