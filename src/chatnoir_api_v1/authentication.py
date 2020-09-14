from collections import deque
from datetime import datetime, timedelta
import ipaddress

from django.conf import settings
from django.core.cache import cache
from django.utils.translation import gettext as _
from rest_framework import authentication, exceptions, permissions

from chatnoir_apikey_management.models import ApiKey


class ApiKeyAuthentication(authentication.BaseAuthentication):
    @staticmethod
    def validate_expiration(api_key):
        if api_key.has_expired:
            raise exceptions.AuthenticationFailed(_('API key has expired.'))

    @staticmethod
    def validate_revocation(api_key):
        if api_key.is_revoked:
            raise exceptions.AuthenticationFailed(_('API key has been revoked.'))

    @staticmethod
    def validate_remote_hosts(api_key, request):
        allowed_hosts = api_key.allowed_remote_hosts_list
        if not allowed_hosts:
            return

        client_ip = request.META['REMOTE_ADDR']
        trust_forward = settings.API_TRUST_X_FORWARDED_FOR or client_ip in ('127.0.0.1', '::1')
        if trust_forward and request.META.get('HTTP_X_FORWARDED_FOR'):
            client_ip = request.META['HTTP_X_FORWARDED_FOR'].split(',')[0].strip()
        client_ip = ipaddress.ip_network(client_ip)

        for host in allowed_hosts:
            if ipaddress.ip_network(host).overlaps(client_ip):
                return

        raise exceptions.PermissionDenied(_('Remote IP not allowed.'))

    @classmethod
    def validate_api_limits(cls, api_key, increment=True):
        limits = api_key.limits_inherited
        if limits == (-1, -1, -1):
            # Entirely unlimited
            return

        cache_key = '.'.join((__name__, cls.__name__, api_key.pk, 'api_quota_used'))

        day_seconds = 60 * 60 * 24
        now = datetime.now()
        bucket_default = (int(now.timestamp()), 0)
        quota_used = cache.get(cache_key, deque())
        month_back = (now - timedelta(seconds=day_seconds * 30)).timestamp()
        week_back = (now - timedelta(seconds=day_seconds * 7)).timestamp()
        day_back = (now - timedelta(seconds=day_seconds)).timestamp()

        # Drop all buckets older than a month
        while quota_used and quota_used[0][0] < month_back:
            quota_used.popleft()

        # Append "today" bucket if needed
        if not quota_used or quota_used[-1][0] < day_back:
            quota_used.append(bucket_default)

        day_used = quota_used[-1][1]
        week_used = 0
        month_used = 0
        for bucket in quota_used:
            month_used += bucket[1]
            if bucket[0] >= week_back:
                week_used += bucket[1]

        def exceeded(u, l):
            return -1 < l <= u

        if exceeded(day_used, limits[0]) or exceeded(week_used, limits[1]) or exceeded(month_used, limits[2]):
            cache.set(cache_key, quota_used, timeout=day_seconds * 30)
            raise exceptions.Throttled(None, _('API request limit exceeded.'))

        if increment:
            quota_used[-1] = (quota_used[-1][0], quota_used[-1][1] + 1)
        cache.set(cache_key, quota_used, timeout=day_seconds * 30)

    def authenticate(self, request):
        if request.method == 'OPTIONS':
            return None

        api_key = request.data.get('apikey') or request.GET.get('apikey')
        if not api_key:
            raise exceptions.NotAuthenticated(_('No API key supplied.'))

        try:
            api_key = ApiKey.objects.get(api_key=api_key)
        except ApiKey.DoesNotExist:
            raise exceptions.NotAuthenticated(_('Invalid API key.'))

        self.validate_expiration(api_key)
        self.validate_revocation(api_key)
        self.validate_remote_hosts(api_key, request)
        self.validate_api_limits(api_key)

        return api_key.user, api_key


def validate_roles(request, roles):
    if not request.user.is_authenticated or not request.auth.roles:
        return False

    for r in request.auth.roles.all():
        if r.role in roles:
            return True

    return False


class HasKeyCreateRole(permissions.BasePermission):
    def has_permission(self, request, view):
        return validate_roles(request, (settings.API_KEY_CREATE_ROLE, settings.API_ADMIN_ROLE))


class HasAdminRole(permissions.BasePermission):
    def has_permission(self, request, view):
        return validate_roles(request, (settings.API_ADMIN_ROLE,))
