"""
Django settings for the ChatNoir Web Cache.
"""

from chatnoir.settings_common import *

APPLICATION_NAME = 'ChatNoir Web Cache'

INSTALLED_APPS = [
    'web_cache.apps.ChatnoirWebCacheConfig',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.staticfiles',
    'corsheaders'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    "corsheaders.middleware.CorsMiddleware",
    'django.middleware.common.CommonMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware'
]

ROOT_URLCONF = 'web_cache.urls'

TEMPLATES[0]['DIRS'].append(os.path.join(BASE_DIR, 'web_cache', 'templates'))

WSGI_APPLICATION = 'web_cache.wsgi.application'

DATABASES = {}

STATICFILES_DIRS = []

try:
    from .local_settings import *
except ImportError:
    pass
