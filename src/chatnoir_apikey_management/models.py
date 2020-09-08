import logging
import uuid

from django.db import IntegrityError, models, transaction
from django.utils.translation import gettext as _


logger = logging.getLogger(__name__)


class ApiUser(models.Model):
    """
    API users associated with an API key.
    """
    class Meta:
        verbose_name = _('API User')
        verbose_name_plural = _('API Users')

    common_name = models.CharField(verbose_name=_('Common Name'), max_length=100)
    email = models.EmailField(verbose_name=_('Email Address'), max_length=200)
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

    api_keys_plain.short_description = _('API Keys')


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

    api_key = models.UUIDField(verbose_name=_('API Key'), primary_key=True, default=uuid.uuid4)
    user = models.ForeignKey(ApiUser, verbose_name=_('API User'), related_name='api_key', on_delete=models.CASCADE)
    parent = models.ForeignKey('self', verbose_name=_('Parent Key'), on_delete=models.CASCADE, null=True, blank=True)
    expires = models.DateField(verbose_name=_('Expiration Date'), null=True, blank=True)
    limits_day = models.IntegerField(verbose_name=_('Daily Limit'), null=True, blank=True)
    limits_week = models.IntegerField(verbose_name=_('Weekly Limit'), null=True, blank=True)
    limits_month = models.IntegerField(verbose_name=_('Monthly Limit'), null=True, blank=True)
    allowed_remote_hosts = models.TextField(verbose_name=_('Allowed Remote Hosts'), null=True, blank=True)
    roles = models.ManyToManyField(ApiKeyRole, verbose_name=_('API Key Roles'), blank=True)

    def __str__(self):
        return '{0} ({1})'.format(self.api_key, self.user.common_name)

    def parent_str(self):
        if not self.parent:
            return ''
        return str(self.parent.api_key)

    def roles_str(self):
        return ','.join([r.role for r in self.roles.all()])

    roles_str.short_description = _('Roles')
    parent_str.short_description = _('Parent Key')


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
    passcode = models.ForeignKey(ApiKeyPasscode, on_delete=models.CASCADE)


class PendingApiUser(models.Model):
    """
    Passcode API users pending activation.
    """
    class Meta:
        unique_together = ('email', 'passcode')
        verbose_name = _('Pending API User')
        verbose_name_plural = _('Pending API Users')

    activation_code = models.UUIDField(verbose_name=_('Activation Code'), default=uuid.uuid4, primary_key=True)
    passcode = models.ForeignKey(ApiKeyPasscode, verbose_name=_('Passcode'), on_delete=models.CASCADE)
    common_name = models.CharField(verbose_name=_('Common Name'), max_length=100)
    email = models.EmailField(verbose_name=_('Email Address'), max_length=200)
    organization = models.CharField(verbose_name=_('Organization'), max_length=100, null=True, blank=True)
    address = models.CharField(verbose_name=_('Address'), max_length=200, null=True, blank=True)
    zip_code = models.CharField(verbose_name=_('ZIP Code'), max_length=50, null=True, blank=True)
    state = models.CharField(verbose_name=_('State'), max_length=50, null=True, blank=True)
    country = models.CharField(verbose_name=_('Country'), max_length=50, null=True, blank=True)

    @staticmethod
    def activate_by_code(activation_code: str):
        """
        :param activation_code: activation code
        :return: activated user or False if activation code does not exist
        """
        try:
            pending_user = PendingApiUser.objects.get(activation_code=activation_code)
            if not pending_user.passcode:
                logger.error('Pending user {} ({}) has no associated passcode.'.format(
                    pending_user.common_name, pending_user.email))
                return False

        except PendingApiUser.DoesNotExist:
            return False

        try:
            with transaction.atomic():
                api_key = ApiKey(api_key=str(uuid.uuid4()), parent=pending_user.passcode.issue_key)
                api_key.save()
                user = ApiUser(
                    api_key=api_key,
                    common_name=pending_user.common_name,
                    email=pending_user.email,
                    organization=pending_user.organization,
                    address=pending_user.address,
                    zip_code=pending_user.zip_code,
                    state=pending_user.state,
                    country=pending_user.country,
                )
                user.save()
                redemption = PasscodeRedemption(api_key=api_key, passcode=pending_user.passcode)
                redemption.save()
                pending_user.delete()
                return user
        except IntegrityError as e:
            logger.error('Error activating user {} ({}):'.format(pending_user.common_name, pending_user.email), e)
            return False
