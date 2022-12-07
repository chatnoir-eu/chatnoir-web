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

import json

from django import template
from django.conf import settings
from django.utils.safestring import mark_safe

from chatnoir_api.authentication import ApiKeyAuthentication

register = template.Library()


@register.filter(name='json')
def json_filter(value):
    return json.dumps(value)


@register.simple_tag
def app_name():
    return settings.APPLICATION_NAME


@register.simple_tag(takes_context=True)
def search_session_apikey(context):
    """
    Get a temporary session API key.
    Using this template tag will invalidate any previous session API key.
    """
    apikey = ApiKeyAuthentication.issue_temporary_session_apikey(context['request'], issuer='web_frontend')
    return mark_safe(json.dumps({
        'token': apikey.api_key,
        'timestamp': int(apikey.issue_date.timestamp()),
        'max_age': int((apikey.expires - apikey.issue_date).total_seconds()) + 1,
        'quota': apikey.limits_day
    }))
