from ipaddress import ip_network

from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


from chatnoir_apikey_management.models import ApiKey, ApiKeyRole


def validate_index_names(index_names, search_version=1):
    for i in index_names:
        if i not in settings.SEARCH_INDEXES or \
                search_version not in settings.SEARCH_INDEXES[i]['compat_search_versions']:
            raise ValidationError(_('\'{}\' is not a valid index.'.format(i)))


def validate_cidr_address(address):
    try:
        ip_network(address)
    except ValueError:
        raise ValidationError(_('Not a valid IP address or network in CIDR notation.'))


def validate_api_role_exists(role):
    try:
        ApiKeyRole.objects.get(role=role)
    except ApiKeyRole.DoesNotExist:
        raise ValidationError(_('Role \'{}\' does not exist.').format(role))


def validate_api_key(data):
    if not data.get('apikey') and not data.get('parent'):
        raise ValidationError(_('Either apikey or parent are required'))

    parent = None
    if data.get('parent'):
        try:
            parent = ApiKey.objects.get(api_key=data['parent'])
        except ApiKey.DoesNotExist:
            raise ValidationError(_('Parent API key does not exist.'))
    elif data.get('apikey'):
        try:
            parent = ApiKey.objects.get(api_key=data['apikey']).parent
        except ApiKey.DoesNotExist:
            pass

    if parent is None:
        raise ValidationError(_('API key has no parent.'))

    parent_limits = parent.limits_inherited
    for i, lim in enumerate(('day', 'week', 'month')):
        if data['limits'][lim] is None or parent_limits[i] < 0:
            continue
        elif data['limits'][lim] > parent_limits[i] or (data['limits'][lim] < 0 and parent_limits[i] >= 0):
            raise ValidationError(_('Request limit for \'{}\' cannot exceed parent request limit.'.format(lim)))

    parent_roles = {r.role for r in parent.roles.all()}
    if settings.API_ADMIN_ROLE not in parent_roles:
        for role in data['roles']:
            if role not in parent_roles:
                raise ValidationError(_('Cannot assign role \'{}\' which you do not possess yourself.'.format(role)))
