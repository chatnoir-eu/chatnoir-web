# Copyright 2022 Janek Bevendorff
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

from django.conf import settings
from chatnoir_search.search import SimpleSearch


def _get_indices(request):
    """List of configured indices."""

    search = SimpleSearch(indices=request.GET.getlist('index'))
    selected = search.selected_indices
    return [{'id': k, 'name': v.get('display_name'), 'selected': k in selected}
            for k, v in search.allowed_indices.items()]


def _get_frontend_settings():
    s = {
        'app_name': settings.APPLICATION_NAME,
        'app_module': settings._wrapped.SETTINGS_MODULE.replace('.settings', ''),
        'search_frontend_url': settings.SEARCH_FRONTEND_URL or '/',
    }
    s.update(settings.FRONTEND_ADDITIONAL_SETTINGS)
    return s


def global_vars(request):
    """Set global template variables."""

    return {
        'indices': _get_indices(request),
        'settings': _get_frontend_settings()
    }
