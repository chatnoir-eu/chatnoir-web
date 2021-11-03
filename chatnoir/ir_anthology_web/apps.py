from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class IRAnthologyWebConfig(AppConfig):
    name = 'ir_anthology_web'
    verbose_name = _('IR Anthology Search')
