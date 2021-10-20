from ipaddress import ip_network

from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
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


def validate_api_key(data, no_parent_ok=False):
    if not data.get('apikey') and not data.get('parent'):
        if no_parent_ok:
            raise ValidationError(_('No API key given.'))
        raise ValidationError(_('Either API key or parent API key are required'))

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
        if no_parent_ok:
            return
        raise ValidationError(_('API key has no parent.'))

    if parent == data.get('apikey'):
        raise ValidationError(_('API key cannot be its own parent.'))

    limits = data.get('limits', {})
    parent_limits = parent.limits_inherited
    for i, lim in enumerate(('day', 'week', 'month')):
        if limits.get(lim) is None or parent_limits[i] < 0:
            continue
        elif limits.get(lim) > parent_limits[i] or (data['limits'][lim] < 0 and parent_limits[i] >= 0):
            raise ValidationError(_('Request limit for "{}" cannot exceed parent request limit.'.format(lim)))

    if data.get('expires'):
        if data['expires'] > parent.expires_inherited:
            raise ValidationError(_('Expiration date cannot be further in the future than parent expiration date.'))
        if data['expires'] < timezone.now():
            raise ValidationError(_('Expiration date cannot be in the past.'))

    parent_roles = {r.role for r in parent.roles.all()}
    if settings.API_ADMIN_ROLE not in parent_roles:
        for role in data.get('roles', []):
            if role not in parent_roles:
                raise ValidationError(_('Cannot assign role "{}" which you do not possess yourself.'.format(role)))
