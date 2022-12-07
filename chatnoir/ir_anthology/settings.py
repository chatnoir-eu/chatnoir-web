"""
Django settings for the IR Anthology Search.
"""

# noinspection PyUnresolvedReferences
from chatnoir.settings import *

APPLICATION_NAME = 'IR Anthology Search'

INSTALLED_APPS = [
    'ir_anthology_web.apps.IRAnthologyWebConfig',
    'ir_anthology_api.apps.IRAnthologyApiConfig',
] + INSTALLED_APPS

ROOT_URLCONF = 'ir_anthology.urls'

WSGI_APPLICATION = 'ir_anthology.wsgi.application'

try:
    from .local_settings import *
except ImportError:
    pass
