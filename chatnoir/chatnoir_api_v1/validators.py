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

from ipaddress import ip_network

from django.conf import settings
from rest_framework.serializers import ValidationError
from django.utils import timezone
from django.utils.translation import gettext as _


from .models import ApiKey, ApiKeyRole


def validate_index_names(index_names, search_version=1):
    for i in index_names:
        if i not in settings.SEARCH_INDICES or \
                search_version not in settings.SEARCH_INDICES[i]['compat_search_versions']:
            raise ValidationError({'index': _('"%s" is not a valid index.') % i}, 'invalid_index')


def validate_cidr_address(address):
    try:
        ip_network(address)
    except ValueError:
        raise ValidationError(_('Not a valid IP address or network in CIDR notation.'), 'invalid_ip')


def validate_api_role_exists(role):
    try:
        ApiKeyRole.objects.get(role=role)
    except ApiKeyRole.DoesNotExist:
        raise ValidationError(_('Role "%s" does not exist.') % role, 'invalid_role')


def validate_api_key(data, no_parent_ok=False):
    if not data.get('apikey') and not data.get('parent'):
        if no_parent_ok:
            raise ValidationError({'apikey': _('No API key given.')})
        raise ValidationError({'apikey': _('Either API key or parent API key are required')})

    parent = None
    if data.get('parent'):
        try:
            parent = ApiKey.objects.get(api_key=data['parent'])
        except ApiKey.DoesNotExist:
            raise ValidationError({'parent': _('Parent API key does not exist.')})
    elif data.get('apikey'):
        try:
            parent = ApiKey.objects.get(api_key=data['apikey']).parent
        except ApiKey.DoesNotExist:
            pass

    if parent is None:
        if no_parent_ok:
            return
        raise ValidationError({'parent': _('API key has no parent.')})

    if parent == data.get('apikey'):
        raise ValidationError({'parent': _('API key cannot be its own parent.')})

    limits = data.get('limits', {})
    parent_limits = parent.limits
    for i, lim in enumerate(('day', 'week', 'month')):
        if limits.get(lim) is None or parent_limits[i] is None:
            # All good if no explicit limit set or parent is unlimited
            continue
        elif parent_limits[i] is not None and limits.get(lim) is not None and limits[lim] > parent_limits[i]:
            # If parent is not unlimited, key limits must be within bounds
            raise ValidationError({
                'limits': {lim: _('Request limit for "%s" cannot exceed parent request limit.') % lim}
            }, 'limit_out_of_bounds')

    if data.get('expires'):
        if parent.expires is not None and data['expires'] > parent.expires:
            raise ValidationError({
                'expires': _('Expiration date cannot be further in the future than parent expiration date.')
            }, 'invalid_date')
        if data['expires'] < timezone.now():
            raise ValidationError({'expires': _('Expiration date cannot be in the past.')}, 'invalid_date')

    parent_roles = {r.role for r in parent.roles.all()}
    if settings.API_ADMIN_ROLE not in parent_roles:
        for role in data.get('roles', []):
            if role not in parent_roles:
                raise ValidationError({
                    'roles': _('Cannot assign role "%s" which you do not possess yourself.') % role
                }, 'invalid_role')
