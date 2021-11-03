from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class IRAnthologyApiConfig(AppConfig):
    name = 'ir_anthology_api_v1'
    verbose_name = _('IR Anthology Search REST API v1')
