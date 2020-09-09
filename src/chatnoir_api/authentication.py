from datetime import datetime, timedelta
import ipaddress

from django.conf import settings
from django.core.cache import cache
from django.utils.translation import gettext as _
from rest_framework import authentication, exceptions, permissions

from chatnoir_apikey_management.models import *


class ApiKeyAuthentication(authentication.BaseAuthentication):
    @staticmethod
    def validate_expiration(api_key):
        if api_key.has_expired:
            raise exceptions.AuthenticationFailed(_('API key has expired.'))

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
    def validate_api_limits(cls, api_key):
        cache_key = '.'.join((__name__, cls.__name__, api_key.pk, 'api_limits'))

        def check_window(window, limit, timeout):
            if limit < 0:
                # unlimited
                return True

            window_key = '.'.join((cache_key, window))
            default = (datetime.now(), 0)
            quota_used = cache.get_or_set(window_key, default, timeout=timeout)
            if datetime.now() - quota_used[0] > timedelta(seconds=timeout):
                # Window has expired
                quota_used = default

            if quota_used[1] > limit:
                return False

            cache.set(window_key, (quota_used[0], quota_used[1] + 1))
            return True

        limits = api_key.limits_inherited
        timeout_base = 60 * 60 * 24
        if check_window('month', limits[2], timeout_base * 30) and \
                check_window('week', limits[1], timeout_base * 7) and \
                check_window('day', limits[0], timeout_base):
            return

        raise exceptions.Throttled(None, _('API request limit exceeded.'))

    def authenticate(self, request):
        api_key = request.data.get('apikey') or request.GET.get('apikey')
        if not api_key:
            raise exceptions.NotAuthenticated(_('No API key supplied.'))

        try:
            api_key = ApiKey.objects.get(api_key=api_key)
        except ApiKey.DoesNotExist:
            raise exceptions.NotAuthenticated(_('Invalid API key.'))

        self.validate_expiration(api_key)
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
