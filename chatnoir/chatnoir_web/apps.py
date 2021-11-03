from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ChatnoirWebConfig(AppConfig):
    name = 'chatnoir_web'
    verbose_name = _('ChatNoir Web Frontend')
