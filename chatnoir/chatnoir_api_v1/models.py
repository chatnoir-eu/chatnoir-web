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

import logging
import uuid
import secrets

from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import IntegrityError, models, transaction
from django.utils import timezone
from django.utils.html import mark_safe
from django.utils.translation import gettext_lazy as _


logger = logging.getLogger(__name__)


def generate_apikey():
    return secrets.token_urlsafe(16)


class ApiUser(models.Model):
    """
    API users associated with an API key.
    """
    class Meta:
        verbose_name = _('API User')
        verbose_name_plural = _('API Users')

    common_name = models.CharField(verbose_name=_('Common Name'), max_length=100)
    email = models.EmailField(verbose_name=_('Email Address'), max_length=200, unique=True)
    organization = models.CharField(verbose_name=_('Organization'), max_length=100, null=True, blank=True)
    address = models.CharField(verbose_name=_('Address'), max_length=200, null=True, blank=True)
    zip_code = models.CharField(verbose_name=_('ZIP Code'), max_length=50, null=True, blank=True)
    state = models.CharField(verbose_name=_('State'), max_length=50, null=True, blank=True)
    country = models.CharField(verbose_name=_('Country'), max_length=50, null=True, blank=True)

    def __str__(self):
        return '{0} ({1})'.format(self.common_name, self.email)

    def str_plain(self):
        return str(self.common_name)

    def api_keys_plain(self):
        return ', '.join([str(a.api_key) for a in self.api_key.all()])

    def api_keys_html(self):
        return mark_safe('<br>'.join([str(a.api_key) for a in self.api_key.all()]))

    api_keys_plain.short_description = _('API Keys')
    api_keys_html.short_description = _('API Keys')

    @property
    def is_anonymous(self):
        return self.pk is None

    @property
    def is_authenticated(self):
        return not self.is_anonymous


class ApiKeyRole(models.Model):
    """
    API key permission roles.
    """
    class Meta:
        verbose_name = _('API Key Role')
        verbose_name_plural = _('API Key Roles')

    role = models.CharField(verbose_name=_('API Key Role'), max_length=255, primary_key=True)

    def __str__(self):
        return self.role


class ApiKey(models.Model):
    """
    API key with limits.
    """
    class Meta:
        verbose_name = _('API Key')
        verbose_name_plural = _('API Keys')

    api_key = models.CharField(verbose_name=_('API Key'), max_length=255, primary_key=True, default=generate_apikey)
    user = models.ForeignKey(ApiUser, verbose_name=_('API User'), related_name='api_key', on_delete=models.CASCADE)
    issue_date = models.DateTimeField(verbose_name=_('Issue Date'), default=timezone.now, null=True, blank=True)
    parent = models.ForeignKey('self', verbose_name=_('Parent Key'), on_delete=models.CASCADE, null=True, blank=True)
    expires = models.DateTimeField(verbose_name=_('Expiration Date'), null=True, blank=True)
    revoked = models.BooleanField(verbose_name=_('Is Revoked'), blank=True, default=False)
    limits_day = models.IntegerField(verbose_name=_('Request Limit Day'), null=True, blank=True)
    limits_week = models.IntegerField(verbose_name=_('Request Limit Week'), null=True, blank=True)
    limits_month = models.IntegerField(verbose_name=_('Request Limit Month'), null=True, blank=True)
    roles = models.ManyToManyField(ApiKeyRole, verbose_name=_('API Key Roles'), blank=True)
    allowed_remote_hosts = models.TextField(verbose_name=_('Allowed Remote Hosts'), null=True, blank=True)
    comment = models.CharField(verbose_name=_('Comment'), max_length=255, blank=True)
    quota_used = models.BinaryField(blank=True, default=b'')

    def __str__(self):
        comment = self.comment or ''
        if comment:
            comment = ''.join((' (', comment, ')'))
        return '{0}: {1}{2}'.format(self.user.common_name, self.api_key, comment)

    def save(self, *args, **kwargs):
        if self.parent and self.api_key == self.parent.api_key:
            raise ValueError('Cannot parent an API key to itself')
        super().save(*args, **kwargs)

    def resolve_inheritance(self, *field_names):
        if self.pk is None:
            raise RuntimeError('Cannot resolve inheritance on unsaved model.')

        cache_key = '.'.join((__name__, self.__class__.__name__, self.pk, ':'.join(field_names)))
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        if len(field_names) < 1:
            raise ValueError('field_names must at least be length 1')

        obj = self
        resolved = {f: getattr(obj, f) for f in field_names if getattr(obj, f)}
        unresolved = {f: None for f in field_names if not getattr(obj, f)}

        while unresolved and obj.parent:
            obj = obj.parent
            for f in set(unresolved.keys()):
                if getattr(obj, f):
                    resolved[f] = getattr(obj, f)
                    del unresolved[f]

        resolved.update(unresolved)
        if len(resolved) == 1:
            val = next(iter(resolved.values()))
            cache.set(cache_key, val)
            return val

        resolved = [resolved[k] for k in field_names]
        cache.set(cache_key, resolved)
        return resolved

    def is_sub_key_of(self, key, strict=True):
        """
        Check if this key is a sub key of another key.

        :param key: parent key
        :param strict: don't treat the key as its own child
        :return: True if ``key`` is a sub key
        """
        if self.pk is None:
            return False

        if self.pk == key:
            return not strict

        parent = self.parent
        while self.parent:
            if parent.api_key == key:
                return True
            parent = parent.parent
        return False

    @property
    def roles_str(self):
        return ', '.join([r.role for r in self.roles.all()])

    @property
    def expires_inherited(self):
        return self.resolve_inheritance('expires')

    @property
    def allowed_remote_hosts_list(self):
        if not self.allowed_remote_hosts:
            return []
        return [h.strip() for h in self.allowed_remote_hosts.split(',')]

    @property
    def limits_inherited(self):
        return tuple(lim if lim is not None else -1
                     for lim in self.resolve_inheritance('limits_day', 'limits_week', 'limits_month'))

    @property
    def has_expired(self):
        expires = self.resolve_inheritance('expires')
        return expires and expires < timezone.now()

    @property
    def is_revoked(self):
        return self.resolve_inheritance('revoked') is True

    @property
    def is_valid(self):
        expires_inherited = self.expires_inherited
        return not self.is_revoked and (not expires_inherited or expires_inherited >= timezone.now())

    @property
    def is_legacy_key(self):
        try:
            uuid.UUID(self.api_key)
            return True
        except (ValueError, TypeError):
            return False

    roles_str.fget.short_description = roles.verbose_name
    expires_inherited.fget.short_description = expires.verbose_name
    is_revoked.fget.short_description = _('Revoked')


class ApiKeyPasscode(models.Model):
    """
    API key issue pass codes.
    """
    class Meta:
        verbose_name = _('API Key Passcode')
        verbose_name_plural = _('API Key Passcodes')

    issue_key = models.ForeignKey(ApiKey, verbose_name=_('Issue Key'), on_delete=models.CASCADE)
    passcode = models.CharField(verbose_name=_('Passcode'), max_length=100, unique=True)
    expires = models.DateField(verbose_name=_('Expiration Date'), null=True, blank=True)

    def __str__(self):
        return str(self.passcode)


class PasscodeRedemption(models.Model):
    """
    List of already redeemed passcodes.
    """
    class Meta:
        unique_together = ('api_key', 'passcode')

    api_key = models.ForeignKey(ApiKey, on_delete=models.CASCADE)
    redemption_date = models.DateTimeField(default=timezone.now)
    passcode = models.ForeignKey(ApiKeyPasscode, on_delete=models.CASCADE)


class PendingApiUser(models.Model):
    """
    Passcode API users pending activation.
    """
    class Meta:
        unique_together = ('email', 'passcode')
        verbose_name = _('Pending API User')
        verbose_name_plural = _('Pending API Users')

    activation_code = models.CharField(verbose_name=_('Activation Code'), max_length=255,
                                       default=generate_apikey, primary_key=True)
    passcode = models.ForeignKey(ApiKeyPasscode, verbose_name=_('Passcode'), on_delete=models.CASCADE,
                                 null=True, blank=True)
    issue_key = models.ForeignKey(ApiKey, verbose_name=_('Issue Key'), on_delete=models.CASCADE, null=True, blank=True)
    common_name = models.CharField(verbose_name=_('Common Name'), max_length=100)
    email = models.EmailField(verbose_name=_('Email Address'), max_length=200)
    organization = models.CharField(verbose_name=_('Organization'), max_length=100, null=True, blank=True)
    address = models.CharField(verbose_name=_('Address'), max_length=200, null=True, blank=True)
    zip_code = models.CharField(verbose_name=_('ZIP Code'), max_length=50, null=True, blank=True)
    state = models.CharField(verbose_name=_('State'), max_length=50, null=True, blank=True)
    country = models.CharField(verbose_name=_('Country'), max_length=50, null=True, blank=True)
    comments = models.TextField(verbose_name=_('Comments'), max_length=200, null=True, blank=True)
    email_verified = models.BooleanField(verbose_name=_('Email verified'), default=False)

    def activate(self):
        """
        Activate pending user.
        """
        try:
            with transaction.atomic():
                user, _ = ApiUser.objects.update_or_create(
                    email=self.email,
                    defaults=dict(
                        common_name=self.common_name,
                        organization=self.organization,
                        address=self.address,
                        zip_code=self.zip_code,
                        state=self.state,
                        country=self.country,
                    )
                )
                issue_key = self.issue_key
                if self.passcode:
                    issue_key = self.passcode.issue_key
                api_key = ApiKey(api_key=generate_apikey(), parent=issue_key, user=user)
                api_key.save()
                if self.passcode:
                    redemption = PasscodeRedemption(api_key=api_key, passcode=self.passcode)
                    redemption.save()
                self.delete()
            return user, api_key
        except IntegrityError as e:
            logger.error('Error activating user %s (%s):', self.common_name, self.email)
            logger.exception(e)
            return None

    @staticmethod
    def activate_by_code(activation_code: str):
        """
        :param activation_code: activation code
        :raise ValidationError: if user has no passcode, email is not verified, or user does not exist
        :return: activated user
        """
        try:
            pending_user = PendingApiUser.objects.get(activation_code=activation_code)
            if not pending_user.passcode:
                raise ValidationError(_('User has no associated passcode.'))
            if not pending_user.email_verified:
                raise ValidationError(_('Email address not verified.'))

            return pending_user.activate()

        except PendingApiUser.DoesNotExist:
            raise ValidationError(_('User does not exist.'))
