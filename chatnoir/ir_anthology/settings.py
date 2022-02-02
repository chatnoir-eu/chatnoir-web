"""
Django settings for the IR Anthology Search.
"""

from chatnoir.settings import *

APPLICATION_NAME = 'IR Anthology Search'

INSTALLED_APPS = [
    'ir_anthology_web.apps.IRAnthologyWebConfig',
    'ir_anthology_api_v1.apps.IRAnthologyApiConfig',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'webpack_loader',
    'rest_framework'
]

ROOT_URLCONF = 'ir_anthology.urls'

TEMPLATES[0]['DIRS'] = [
    os.path.join(BASE_DIR, 'ir_anthology_web', 'templates'),
    os.path.join(BASE_DIR, 'chatnoir_web', 'templates')
]

WSGI_APPLICATION = 'ir_anthology.wsgi.application'

try:
   from .local_settings import *
except ImportError:
    pass
