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

import base64
from datetime import datetime, timedelta, timezone as dt_timezone
import ipaddress
import json
import pickle
import secrets
from hashlib import sha256

from django.conf import settings
from django.core import serializers
from django.utils import timezone
from django.utils.translation import gettext as _
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from rest_framework import authentication, exceptions as rest_exceptions, permissions

from .models import ApiKey


class ApiKeyAuthentication(authentication.BaseAuthentication):
    SESSION_APIKEY_KEY = 'session_api_key'
    SIGNED_TOKEN_PREFIX = 'sig:'

    @staticmethod
    def _b64decode(data):
        if isinstance(data, str):
            data = data.encode()
        return base64.urlsafe_b64decode(data + b'=' * (-len(data) % 4))

    @staticmethod
    def _api_key_seed(private_key: str | bytes):
        private_bytes = private_key.encode() if isinstance(private_key, str) else private_key
        if len(private_bytes) == 32:
            return private_bytes
        return sha256(private_bytes).digest()

    @classmethod
    def _canonical_signed_token_payload(cls, payload):
        signed_payload = {k: v for k, v in payload.items() if k != 'signature'}
        return json.dumps(signed_payload, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()

    @staticmethod
    def _b64encode(data):
        if isinstance(data, str):
            data = data.encode()
        return base64.urlsafe_b64encode(data).decode().rstrip('=')

    @staticmethod
    def _isoformat_z(value):
        return value.astimezone(dt_timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')

    @classmethod
    def _authenticate_signed_token(cls, api_key_token_str):
        if not api_key_token_str.startswith(cls.SIGNED_TOKEN_PREFIX):
            return None

        try:
            token_data = json.loads(cls._b64decode(api_key_token_str[len(cls.SIGNED_TOKEN_PREFIX):]).decode())
            key_id = token_data['key_id']
            valid_from = datetime.fromisoformat(token_data['valid_from'].replace('Z', '+00:00'))
            valid_until = datetime.fromisoformat(token_data['valid_until'].replace('Z', '+00:00'))
            nonce = token_data['nonce']
            signature = cls._b64decode(token_data['signature'])
        except (KeyError, TypeError, ValueError, json.JSONDecodeError):
            raise rest_exceptions.NotAuthenticated(_('Invalid API key token.'))

        if not isinstance(key_id, str) or not key_id or not isinstance(nonce, str) or not nonce:
            raise rest_exceptions.NotAuthenticated(_('Invalid API key token.'))

        if timezone.is_naive(valid_from) or timezone.is_naive(valid_until) or valid_until < valid_from:
            raise rest_exceptions.NotAuthenticated(_('Invalid API key token.'))

        now = timezone.now()
        if now < valid_from:
            raise rest_exceptions.AuthenticationFailed(_('API key token is not valid yet.'), 'not_yet_valid')
        if now > valid_until:
            raise rest_exceptions.AuthenticationFailed(_('API key token has expired.'), 'expired')

        message = cls._canonical_signed_token_payload(token_data)
        try:
            api_key = ApiKey.objects.prefetch_related('roles').get(key_id=key_id)
        except ApiKey.DoesNotExist:
            raise rest_exceptions.NotAuthenticated(_('Invalid API key token.'))

        public_key = Ed25519PrivateKey.from_private_bytes(cls._api_key_seed(api_key.private_key + nonce)).public_key()
        try:
            public_key.verify(signature, message)
        except InvalidSignature:
            raise rest_exceptions.NotAuthenticated(_('Invalid API key token.'))

        api_key._auth_credential = api_key_token_str
        api_key._auth_via_signature = True
        return api_key

    @classmethod
    def create_signed_apikey_token(cls, api_key, validity=None):
        """
        Create a new signed API key token for the given API key.

        :param api_key: API key model object
        :param validity: validity period in seconds (default from settings if ``None``)
        """
        if not api_key.user_id:
            return None
        if not validity:
            validity = min(settings.API_KEY_TOKEN_DEFAULT_AGE, settings.API_KEY_TOKEN_MAX_AGE)

        valid_from = datetime.now(dt_timezone.utc)
        valid_until = valid_from + timedelta(seconds=validity)
        nonce = secrets.token_urlsafe(16)
        payload = {
            'key_id': api_key.key_id,
            'valid_from': cls._isoformat_z(valid_from),
            'valid_until': cls._isoformat_z(valid_until),
            'nonce': nonce,
        }
        message = cls._canonical_signed_token_payload(payload)
        signature = Ed25519PrivateKey.from_private_bytes(cls._api_key_seed(api_key.private_key + nonce)).sign(message)
        payload['signature'] = cls._b64encode(signature)
        return cls.SIGNED_TOKEN_PREFIX + cls._b64encode(json.dumps(payload, sort_keys=True, separators=(',', ':')))

    @staticmethod
    def validate_expiration(api_key):
        if api_key.has_expired:
            raise rest_exceptions.AuthenticationFailed(_('API key has expired.'), 'expired')

    @staticmethod
    def validate_revocation(api_key):
        if api_key.revoked:
            raise rest_exceptions.AuthenticationFailed(_('API key has been revoked.'), 'revoked')

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

        raise rest_exceptions.PermissionDenied(_('Remote IP not allowed.'), 'not_allowed')

    @classmethod
    def validate_api_limits(cls, api_key, increment=True):
        limits = api_key.limits
        if limits == (None, None, None):
            # Entirely unlimited
            return

        day_seconds = 60 * 60 * 24
        now = datetime.now()
        bucket_default = (int(now.timestamp()), 0)
        month_back = int((now - timedelta(seconds=day_seconds * 30)).timestamp())
        week_back = int((now - timedelta(seconds=day_seconds * 7)).timestamp())
        day_back = int((now - timedelta(seconds=day_seconds)).timestamp())

        if not api_key.quota_used:
            quota_used = [bucket_default]
        else:
            # Load pickled quota and drop buckets older than a month
            quota_used = [q for q in pickle.loads(api_key.quota_used) if q[0] >= month_back]

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
            return l is not None and l <= u

        quota_exceeded = exceeded(day_used, limits[0]) or \
            exceeded(week_used, limits[1]) or exceeded(month_used, limits[2])

        if increment and not quota_exceeded:
            quota_used[-1] = (quota_used[-1][0], quota_used[-1][1] + 1)

        pickled = pickle.dumps(quota_used)
        if api_key.quota_used != pickled:
            api_key.quota_used = pickled
            if api_key._state.db:
                api_key.save()

        if quota_exceeded:
            raise rest_exceptions.Throttled(None, _('API request limit exceeded.'), 'quota_exceeded')

    @classmethod
    def _save_session_apikey(cls, request, api_key):
        """Store serialized API key in session."""
        request.session[cls.SESSION_APIKEY_KEY] = serializers.serialize('json', [api_key])

    @classmethod
    def _get_session_apikey(cls, request):
        """Retrieve API key from session or return ``None`` if no API key ist set."""
        for serialized in serializers.deserialize('json', request.session.get(cls.SESSION_APIKEY_KEY, '[]')):
            serialized.object.save = lambda *_, **__: None
            return serialized.object

    def authenticate(self, request):
        if request.method == 'OPTIONS':
            return None

        bearer = authentication.get_authorization_header(request).decode().split()
        if len(bearer) == 2 and bearer[0].lower() in ['bearer', 'token']:
            api_key_str = bearer[1]
        else:
            api_key_str = request.data.get('apikey') or request.GET.get('apikey')

        if not api_key_str:
            raise rest_exceptions.NotAuthenticated(_('No API key supplied.'))

        # Test for temporary session API keys first
        api_key = self._get_session_apikey(request)
        if api_key and (not hasattr(api_key, 'api_key') or api_key.api_key != api_key_str):
            api_key = None
        is_temporary_key = api_key is not None

        # Fall back to regular API keys if temporary session key is invalid or unset
        if not api_key:
            api_key = self._authenticate_signed_token(api_key_str)
            if not api_key:
                try:
                    api_key = ApiKey.objects.get(api_key=api_key_str)
                except ApiKey.DoesNotExist:
                    raise rest_exceptions.NotAuthenticated(_('Invalid API key.'))

        self.validate_expiration(api_key)
        self.validate_revocation(api_key)
        self.validate_remote_hosts(api_key, request)
        self.validate_api_limits(api_key)

        if not hasattr(api_key, '_auth_credential'):
            api_key._auth_credential = api_key.api_key

        if is_temporary_key:
            # Store updated API limits
            self._save_session_apikey(request, api_key)

        return api_key.user, api_key

    @classmethod
    def issue_temporary_session_apikey(cls, request, validity=300, request_limit=10,
                                       issuer=None, parent=None, user=None):
        """
        Issue a temporary session API key. The key will be stored in the session automatically.

        :param request: HTTP requests with initialized session object
        :param validity: API key validity in seconds
        :param request_limit: request quota for this API key
        :param issuer: internal API key issuer identifier
        :param parent: parent API key (default: unparented)
        :param user: user which to attach the key to (default: anonymous)
        :return: temporary API key
        """
        api_key = ApiKey(
            parent=parent,
            issuer=issuer,
            user=user,
            expires=timezone.now() + timedelta(seconds=validity),
            limits_day=request_limit,
            limits_week=request_limit,
            limits_month=request_limit
        )
        api_key.save = lambda *_, **__: None
        cls._save_session_apikey(request, api_key)
        return api_key


class HasKeyCreateRole(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.auth and request.auth.can_issue_keys


class HasAdminRole(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.auth and request.auth.is_admin_key
