"""
Django settings for the IR Anthology Search.
"""

from chatnoir.settings import *

APPLICATION_NAME = 'IR Anthology Search'

INSTALLED_APPS.extend([
    'ir_anthology_web.apps.IRAnthologyWebConfig',
    'ir_anthology_api_v1.apps.IRAnthologyApiConfig'
])

ROOT_URLCONF = 'ir_anthology.urls'

TEMPLATES[0]['DIRS'] = [
    os.path.join(BASE_DIR, 'ir_anthology_web', 'templates'),
    os.path.join(BASE_DIR, 'chatnoir_web', 'templates')
]

try:
   from .local_settings import *
except ImportError:
    pass
