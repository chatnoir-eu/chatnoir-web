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
    'query_console': {
        'class': 'logging.StreamHandler',
        'formatter': 'query.console',
    },
    'logstash': {
        'class': 'chatnoir.logging.LogstashUDPHandler',
        'host': 'localhost',
        'port': 3334
    }
})
LOGGING['formatters'].update({
    'query.console': {
        '()': 'chatnoir.logging.QueryConsoleFormatter',
    }
})
LOGGING['loggers'].update({
    'query_log': {
        'handlers': ['query_console', 'logstash'],
        'propagate': False,
    }
})

# Cache frontend URL (should be a different origin than the search frontend to avoid cookie leakage)
CACHE_FRONTEND_URL = 'http://127.0.0.1:8001'

try:
    from .local_settings import *
except ImportError:
    import logging
    logging.getLogger(__name__).error('No local_settings.py found. Loading (insecure) default config.')
