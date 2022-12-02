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
        'port': 3333
    }
})
LOGGING['loggers'].update({
    'query_log': {
        'handlers': ['logstash'],
        'propagate': False,
    }
})

try:
    from .local_settings import *
except ImportError:
    raise RuntimeError("Could not find local_settings.py.")
