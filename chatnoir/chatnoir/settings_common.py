"""
Django settings shared by all ChatNoir apps.
"""

import os

# General settings
APPLICATION_NAME = 'ChatNoir'
DEBUG = False
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# HTTP security settings
ALLOWED_HOSTS = ['*']
X_FRAME_OPTIONS = 'SAMEORIGIN'
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Strict'
CSRF_USE_SESSIONS = False
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = 'Strict'
CSRF_COOKIE_NAME = 'csrftoken'
CSRF_HEADER_NAME = 'HTTP_X_CSRF_TOKEN'
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
        "Accept",
        "Authorization",
        "Content-Type",
        "User-Agent",
        "X-Requested-With",
        CSRF_HEADER_NAME[5:].replace('_', '-').title()
    ]
CORS_ALLOW_METHODS = ['HEAD', 'GET', 'POST', 'OPTIONS']

# Email settings
EMAIL_HOST = 'localhost'
SERVER_EMAIL = 'no-reply@localhost'
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_SUBJECT_PREFIX = ''
MANAGERS = []


# Application definition
INSTALLED_APPS = [
    'chatnoir_frontend.apps.ChatnoirWebConfig',
    'chatnoir_api.apps.ChatnoirApiConfig',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'chatnoir_frontend.apps.ChatnoirStaticFilesConfig',
    'corsheaders',
    'rest_framework',
    'solo',
    'django_minify_html',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    "corsheaders.middleware.CorsMiddleware",
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_minify_html.middleware.MinifyHtmlMiddleware',
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
    'DEFAULT_CONTENT_NEGOTIATION_CLASS': 'chatnoir_api.negotiation.FallbackContentNegotiation',
    'EXCEPTION_HANDLER': 'chatnoir_api.views.api_exception_handler'
}

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'chatnoir_frontend', 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
            'libraries': {}
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
    os.path.join(BASE_DIR, '..', 'chatnoir_ui', 'dist')
]

# Elasticsearch backend settings (override me)
ELASTICSEARCH_PROPERTIES = {
    'hosts': ['localhost:9200'],
    'retry_on_timeout': True,
    "use_ssl": True,
    "api_key": ["apikey", "secret"]
}

# Search index settings (override me)
SEARCH_INDICES = {
    'index_shorthand': {                # Index shorthand for referencing it in ChatNoir
        'index': '',                    # Elasticsearch index name
        'warc_index': '',               # Elasticsearch WARC offset index
        'warc_bucket': '',              # WARC S3 bucket
        'warc_uuid_prefix': '',         # WARC document UUID prefix
        'display_name': '',             # Friendly index name
        'source_url': '',               # URL to upstream source dataset
        'compat_search_versions': [1],  # Compatible search versions (so far always 1)
        'default': True                 # Whether this is the default index (optional)
    }
}

# Additional settings to pass to the JavaScript frontend (all settings in this are user-readable!)
FRONTEND_ADDITIONAL_SETTINGS = {}
