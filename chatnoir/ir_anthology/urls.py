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
from django.contrib import admin
from django.views.generic import RedirectView

app_name = 'ir_anthology'

urlpatterns = [
    path(r'', include('ir_anthology_web.urls')),
    path(r'api/', RedirectView.as_view(url=reverse_lazy('api_v1:api-root'))),
    path(r'api/v1/', include('ir_anthology_api_v1.urls')),
    path(r'apikey/admin/', admin.site.urls),
]
