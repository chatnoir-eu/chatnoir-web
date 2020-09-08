from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ChatnoirApikeyManagementConfig(AppConfig):
    name = 'chatnoir_apikey_management'
    verbose_name = _('API Key Management')
