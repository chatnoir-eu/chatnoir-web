"""
Django settings for the ChatNoir Web Frontend not shared by other apps.
"""

from .settings_common import *

# URL routes config
ROOT_URLCONF = 'chatnoir.urls'

# WSGI app entrypoint
WSGI_APPLICATION = 'chatnoir.wsgi.application'

# Cache
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'chatnoir_cache',
        'TIMEOUT': 120
    }
}

# Logging configuration (should be adjusted in local_settings.py)
LOGGING['handlers'].update({
    'logstash': {
        'class': 'chatnoir.logging.LogstashUDPHandler',
        'host': 'localhost',
        'port': 3334
    }
})
LOGGING['loggers'].update({
    'query_log': {
        'handlers': ['logstash'],
        'propagate': False,
    }
})

# Cache frontend URL (should be a different origin than the search frontend to avoid cookie leakage)
CACHE_FRONTEND_URL = 'http://127.0.0.1:8001'

# Template options
TEMPLATES[0]['OPTIONS']['context_processors'].append('chatnoir_frontend.context_processors.global_vars')
TEMPLATES[0]['OPTIONS']['libraries'].update({
    'chatnoir_tags': 'chatnoir_frontend.templatetags'
})

# API roles
API_ADMIN_ROLE = 'admin'
API_KEYCREATE_ROLE = 'keycreate'
API_NOLOG_ROLE = 'nolog'

# Set to true if running behind a proxy
API_TRUST_X_FORWARDED_FOR = False

try:
    from .local_settings import *
except ImportError:
    import logging
    logging.getLogger(__name__).error('No local_settings.py found. Loading (insecure) default config.')
