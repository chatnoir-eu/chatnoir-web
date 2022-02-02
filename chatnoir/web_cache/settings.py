"""
Django settings for the ChatNoir Web Cache.
"""

from chatnoir.settings import *

APPLICATION_NAME = 'ChatNoir Web Cache'
DEBUG = True

CSRF_USE_SESSIONS = False

# Application definition
INSTALLED_APPS = [
    'web_cache.apps.ChatnoirWebCacheConfig',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.staticfiles',
    'corsheaders'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    "corsheaders.middleware.CorsMiddleware",
    'django.middleware.common.CommonMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware'
]

ROOT_URLCONF = 'web_cache.urls'

TEMPLATES[0]['DIRS'] = [
    os.path.join(BASE_DIR, 'web_cache', 'templates'),
    os.path.join(BASE_DIR, 'chatnoir_web', 'templates')
]

WSGI_APPLICATION = 'web_cache.wsgi.application'

DATABASES = {
    'default': {}
}

STATICFILES_DIRS = []

try:
   from .local_settings import *
except ImportError:
    pass
