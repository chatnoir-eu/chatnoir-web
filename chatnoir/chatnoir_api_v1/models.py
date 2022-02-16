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

from concurrent.futures import ThreadPoolExecutor
import ipaddress
import logging
import re
import uuid

from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.mail import EmailMultiAlternatives
from django.db import IntegrityError, models, transaction
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.utils.html import mark_safe
from django.utils.translation import gettext_lazy as _
from django_countries.fields import CountryField

logger = logging.getLogger(__name__)


def generate_apikey():
    return get_random_string(32)


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
    country = CountryField(verbose_name=_('Country'), max_length=50, null=True, blank=True)

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
    roles = models.ManyToManyField(ApiKeyRole, verbose_name=_('API Key Roles'), blank=True)
    allowed_remote_hosts = models.TextField(verbose_name=_('Allowed Remote Hosts'), null=True, blank=True)
    comments = models.TextField(verbose_name=_('Comments'), blank=True)
    quota_used = models.BinaryField(blank=True, default=b'')

    # Inherited fields
    _expires = models.DateTimeField(verbose_name=_('Expiration Date'), null=True, blank=True, db_column='expires')
    _revoked = models.BooleanField(verbose_name=_('Revoked'), blank=True, default=False, db_column='revoked')
    _limits_day = models.PositiveIntegerField(verbose_name=_('Request Limit Day'), null=True,
                                              blank=True, db_column='limits_day')
    _limits_week = models.PositiveIntegerField(verbose_name=_('Request Limit Week'), null=True,
                                               blank=True, db_column='limits_week')
    _limits_month = models.PositiveIntegerField(verbose_name=_('Request Limit Month'), null=True,
                                                blank=True, db_column='limits_month')

    class _Inherited:
        def __init__(self):
            self.expires = None
            self.revoked = None
            self.limits_day = None
            self.limits_week = None
            self.limits_month = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._inherited = self._Inherited()

    @classmethod
    def from_db(cls, *args, **kwargs):
        instance = super().from_db(*args, **kwargs)
        # noinspection PyProtectedMember
        instance._resolve_inheritance()
        return instance

    def refresh_from_db(self, *args, **kwargs):
        super().refresh_from_db(*args, **kwargs)
        self._resolve_inheritance()

    def clean(self):
        if self.allowed_remote_hosts:
            try:
                for ip in self.allowed_remote_hosts_list:
                    self.clean_fields()
                    ipaddress.ip_network(ip)
            except ValueError as e:
                raise ValidationError({'allowed_remote_hosts': e}, 'invalid_ip')

    def save(self, *args, **kwargs):
        if self.parent and self.api_key == self.parent.api_key:
            raise ValueError('Cannot parent an API key to itself')

        # Normalize list of allowed remote hosts
        if self.allowed_remote_hosts:
            self.allowed_remote_hosts = '\n'.join(set(self.allowed_remote_hosts_list))

        super().save(*args, **kwargs)
        self._resolve_inheritance()

    def _resolve_inheritance(self):
        """Resolve inherited field values and cache them."""
        if self.pk is None:
            raise RuntimeError('Cannot resolve inheritance on unsaved model.')

        if not self.parent:
            return

        cache_key = '.'.join((__name__, self.__class__.__name__, self.pk))
        cached = cache.get(cache_key)
        if cached is not None:
            self._inherited = cached
            return

        self._inherited = self._Inherited()
        field_names = [f for f in dir(self._inherited) if not f.startswith('_')]

        for f in field_names:
            self_val = getattr(self, '_' + f)
            parent_val = getattr(self.parent, f)
            setattr(self._inherited, f, parent_val)
            if self_val is not None:
                setattr(self._inherited, f, getattr(self, f))

        cache.set(cache_key, self._inherited)

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
    def expires(self):
        if self._inherited.expires is not None:
            return min(self._inherited.expires, self._expires or self._inherited.expires)
        return self._expires

    @expires.setter
    def expires(self, expires):
        self._inherited.expires = expires
        self._expires = expires

    expires.fget.short_description = _expires.verbose_name

    @property
    def revoked(self):
        if self._inherited.revoked is not None:
            return (self._inherited.revoked is True) or (self._revoked is True)
        return self._revoked

    @revoked.setter
    def revoked(self, revoked):
        self._inherited.revoked = revoked
        self._revoked = revoked

    revoked.fget.boolean = True
    revoked.fget.short_description = _revoked.verbose_name

    @property
    def limits_day(self):
        if self._inherited.limits_day is not None:
            return min(self._inherited.limits_day, self._limits_day or self._inherited.limits_day)
        return self._limits_day

    @limits_day.setter
    def limits_day(self, limits_day):
        self._inherited.limits_day = limits_day
        self._limits_day = limits_day

    limits_day.fget.short_description = _limits_day.verbose_name

    @property
    def limits_week(self):
        if self._inherited.limits_week is not None:
            return min(self._inherited.limits_week, self._limits_week or self._inherited.limits_week)
        return self._limits_week

    @limits_week.setter
    def limits_week(self, limits_week):
        self._inherited.limits_week = limits_week
        self._limits_week = limits_week

    limits_week.fget.short_description = _limits_week.verbose_name

    @property
    def limits_month(self):
        if self._inherited.limits_month is not None:
            return min(self._inherited.limits_month, self._limits_month or self._inherited.limits_month)
        return self._limits_month

    @limits_month.setter
    def limits_month(self, limits_month):
        self._inherited.limits_month = limits_month
        self._limits_month = limits_month

    limits_month.fget.short_description = _limits_month.verbose_name

    @property
    def limits(self):
        """API key request limits as (day, week, month) tuple."""
        return self.limits_day, self.limits_week, self.limits_month

    @property
    def has_expired(self):
        """True if API keys has an expiry date in the past."""
        return self.expires is not None and self.expires <= timezone.now()

    has_expired.fget.boolean = True
    has_expired.fget.short_description = _('Expired')

    @property
    def valid(self):
        """True if API key has not expired and has not been revoked."""
        return not self.has_expired and not self.revoked

    valid.fget.boolean = True
    valid.fget.short_description = _('Valid')

    @property
    def allowed_remote_hosts_list(self):
        if not self.allowed_remote_hosts:
            return []
        return re.split(r'[\s;,]+', self.allowed_remote_hosts.strip())

    def __str__(self):
        if self.comments:
            key = f'{self.comments} ({self.api_key})'
        else:
            key = self.api_key
        return f'{self.user.common_name}: {key}'

    @property
    def roles_str(self):
        """API key roles as comma-separated string."""
        return ', '.join([r.role for r in self.roles.all()])

    roles_str.fget.short_description = roles.verbose_name

    @property
    def is_legacy_key(self):
        try:
            uuid.UUID(self.api_key)
            return True
        except (ValueError, TypeError):
            return False

    is_legacy_key.fget.boolean = True
    is_legacy_key.fget.short_description = _('Legacy Key')


class ApiKeyPasscode(models.Model):
    """
    API key issue pass codes.
    """
    class Meta:
        verbose_name = _('API Passcode')
        verbose_name_plural = _('API Passcodes')

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
        verbose_name = _('API Passcode Redemption Log')
        verbose_name_plural = _('API Passcode Redemption Log')

    api_key = models.ForeignKey(ApiKey, on_delete=models.CASCADE)
    redemption_date = models.DateTimeField(default=timezone.now)
    passcode = models.ForeignKey(ApiKeyPasscode, on_delete=models.CASCADE)


SEND_MAIL_EXECUTOR = ThreadPoolExecutor(max_workers=20)


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
    country = CountryField(verbose_name=_('Country'), max_length=50, null=True, blank=True)
    comments = models.TextField(verbose_name=_('Comments'), max_length=200, null=True, blank=True)
    email_verified = models.BooleanField(verbose_name=_('Email verified'), default=False)

    def user_exists(self):
        """
        Check whether a user with the email address of this pending user already exists.
        """
        try:
            ApiUser.objects.get(email=self.email)
            return True
        except ApiUser.DoesNotExist:
            return False

    user_exists.short_description = _('User exists')
    user_exists.boolean = True

    def generate_activation_code(self, save=True):
        """
        Generate and set a random activation code for the user that can be used in a verification email.

        :param save: save the model afterwards with the new code
        :return: activation code as a string
        """
        self.activation_code = get_random_string(length=36)
        if save:
            self.save()
        return self.activation_code

    def send_verification_mail(self, verification_url):
        """
        Send an email with a verification/activation link to the user.

        :param verification_url: absolute verification URL to embed into the email
        :raises RuntimeError: if user has no activation code (use :meth:`generate_activation_code` for that)
        """
        if not self.activation_code:
            raise RuntimeError('Trying to send verification email, but user has no activation code.')

        mail_context = {
            'app_name': settings.APPLICATION_NAME,
            'common_name': self.common_name,
            'verification_url': verification_url
        }
        mail_content_plain = render_to_string('email/apikey_verification.txt', mail_context)
        mail_content_html = render_to_string('email/apikey_verification.html', mail_context)
        mail = EmailMultiAlternatives(
            _('Complete your %(appname)s API key request') % {'appname': settings.APPLICATION_NAME},
            mail_content_plain,
            f'{settings.APPLICATION_NAME} <{settings.SERVER_EMAIL}>',
            [self.email]
        )
        mail.attach_alternative(mail_content_html, 'text/html')
        SEND_MAIL_EXECUTOR.submit(mail.send)

    def delete(self, using=None, keep_parents=False, email_reason=None):
        """
        Delete pending API user.

        If you are deleting the user without migrating them to a permanent API user, you
        can specify a reason which will be emailed to the user to inform them why their
        API key request was denied.

        :param using: DB alias
        :param keep_parents: keep parent model's data
        :param email_reason: if set, user will be notified by email with this reason phrase
        """
        if email_reason:
            mail_context = {
                'app_name': settings.APPLICATION_NAME,
                'common_name': self.common_name,
                'reason': email_reason
            }
            mail_content_plain = render_to_string('email/apikey_denied.txt', mail_context)
            mail_content_html = render_to_string('email/apikey_denied.html', mail_context)
            mail = EmailMultiAlternatives(
                _('Your %(appname)s API key request') % {'appname': settings.APPLICATION_NAME},
                mail_content_plain,
                f'{settings.APPLICATION_NAME} <{settings.SERVER_EMAIL}>',
                [self.email]
            )
            mail.attach_alternative(mail_content_html, 'text/html')
            SEND_MAIL_EXECUTOR.submit(mail.send)

        return super().delete(using, keep_parents)

    @staticmethod
    def verify_email_by_activation_code(activation_code):
        """
        Try to verify a user's email address with the given activation code.

        On success, this will only mark the user's email as verified. The user themselves will not be
        activated (this has to be done explicitly with :meth:`activate`).

        :param activation_code: the user's activation code
        :return: the pending user model on success or `None` if code is invalid or `False` email already activated
        """
        try:
            pending_user = PendingApiUser.objects.get(activation_code=activation_code)
            if pending_user.email_verified:
                # Email already verified
                return False

            with transaction.atomic():
                pending_user.email_verified = True
                pending_user.save(force_update=True)
            return pending_user

        except PendingApiUser.DoesNotExist:
            return None

    def activate(self, send_email=False):
        """
        Activate the pending user and optionally send a confirmation email to the user.

        :param send_email: send a confirmation email with the new API key to the user
        """
        try:
            with transaction.atomic():
                user, created = ApiUser.objects.update_or_create(
                    email=self.email,
                    defaults=dict(
                        common_name=self.common_name,
                        organization=self.organization,
                        address=self.address,
                        zip_code=self.zip_code,
                        state=self.state,
                        country=self.country
                    )
                )
                issue_key = self.issue_key
                if self.passcode:
                    issue_key = self.passcode.issue_key
                api_key = ApiKey(api_key=generate_apikey(), parent=issue_key, user=user, comments=self.comments)
                api_key.save()
                if self.passcode and not self.issue_key:
                    redemption = PasscodeRedemption(api_key=api_key, passcode=self.passcode)
                    redemption.save()
                self.delete()

            if send_email:
                mail_context = {
                    'app_name': settings.APPLICATION_NAME,
                    'common_name': user.common_name,
                    'api_key': api_key.api_key
                }
                mail_content_plain = render_to_string('email/apikey_confirmation.txt', mail_context)
                mail_content_html = render_to_string('email/apikey_confirmation.html', mail_context)
                mail = EmailMultiAlternatives(
                    _('Your %(appname)s API key') % {'appname': settings.APPLICATION_NAME},
                    mail_content_plain,
                    f'{settings.APPLICATION_NAME} <{settings.SERVER_EMAIL}>',
                    [user.email]
                )
                mail.attach_alternative(mail_content_html, 'text/html')
                SEND_MAIL_EXECUTOR.submit(mail.send)

            return user, api_key
        except IntegrityError as e:
            logger.error('Error activating user %s (%s):', self.common_name, self.email)
            logger.exception(e)
            return None
