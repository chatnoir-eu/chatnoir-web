from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ChatnoirApiConfig(AppConfig):
    name = 'chatnoir_api_v1'
    verbose_name = _('ChatNoir REST API v1')
