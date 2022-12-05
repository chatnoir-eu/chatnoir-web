"""
Django settings shared by all ChatNoir apps.
"""

import os

# General settings
APPLICATION_NAME = 'ChatNoir'
DEBUG = False
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ALLOWED_HOSTS = ['*']
X_FRAME_OPTIONS = 'SAMEORIGIN'
CSRF_USE_SESSIONS = True
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG

# Email settings
EMAIL_HOST = 'localhost'
SERVER_EMAIL = 'no-reply@localhost'
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_SUBJECT_PREFIX = ''
MANAGERS = []

# Application definition
INSTALLED_APPS = [
    'chatnoir_web.apps.ChatnoirWebConfig',
    'chatnoir_api_v1.apps.ChatnoirApiConfig',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'webpack_loader',
    'rest_framework',
    'solo'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    "corsheaders.middleware.CorsMiddleware",
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware'
]

REST_FRAMEWORK = {
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.URLPathVersioning',
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer'
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser'
    ],
    'DEFAULT_CONTENT_NEGOTIATION_CLASS': 'chatnoir_api_v1.negotiation.FallbackContentNegotiation',
    'EXCEPTION_HANDLER': 'chatnoir_api_v1.views.api_exception_handler'
}

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'chatnoir_web', 'templates')
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Logging configuration (should be adjusted in local_settings.py)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'django.server': {
            '()': 'django.utils.log.ServerFormatter',
            'format': '[{server_time}] {message}',
            'style': '{',
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
        'django.server': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'django.server',
        }
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
        'django.server': {
            'handlers': ['django.server'],
            'level': os.getenv('DJANGO_SERVER_LOG_LEVEL', os.getenv('DJANGO_LOG_LEVEL', 'INFO')),
            'propagate': False,
        }
    }
}

# Internationalization
# https://docs.djangoproject.com/en/2.0/topics/i18n/
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True
USE_THOUSAND_SEPARATOR = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, '..', 'chatnoir_static')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, '..', 'chatnoir_ui', 'dist'),
    os.path.join(BASE_DIR, 'chatnoir_web', 'static')
]

# Webpack loader
WEBPACK_LOADER = {
    'DEFAULT': {
        'CACHE': not DEBUG,
        'STATS_FILE': os.path.join(BASE_DIR, '..', 'chatnoir_ui', 'webpack-stats.json'),
        'POLL_INTERVAL': 0.1,
        'IGNORE': [r'.+\.hot-update.js', r'.+\.map'],
    }
}

# Elasticsearch backend settings (override me)
ELASTICSEARCH_PROPERTIES = {
    'hosts': ['localhost:9200'],
    'retry_on_timeout': True,
    "use_ssl": True,
    "api_key": ["apikey", "secret"]
}

# S3 backend settings (override me)
S3_ENDPOINT_PROPERTIES = {
    "endpoint_url": "http://localhost",
    "aws_access_key_id": "access_key",
    "aws_secret_access_key": "secret_key"
}

# Search index settings (override me)
SEARCH_INDICES = {
    'index_shorthand_name': {
        'index': 'index_internal_name',
        'warc_index': 'warc_meta_index_name',
        'warc_bucket': 's3_warc_bucket_name',
        'warc_uuid_prefix': 'webis-uuid-prefix',
        'display_name': 'Human-readable display name',
        'compat_search_versions': [1]
    }
}

# Cache frontend URL (should be different origin to avoid cookie leakage)
CACHE_FRONTEND_URL = 'http://127.0.0.2:8000'

if os.getenv('DJANGO_SETTINGS_MODULE') != 'chatnoir.settings':
    try:
        from .local_settings import *
    except ImportError:
        raise RuntimeError("Could not find local_settings.py.")
