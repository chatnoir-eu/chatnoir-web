"""
Django settings for ChatonIR.
"""

from chatnoir.settings import *

APPLICATION_NAME = 'IR Anthology Search'

INSTALLED_APPS.append('ir_anthology_web.apps.IRAnthologyWebConfig')

ROOT_URLCONF = 'ir_anthology.urls'
# STATICFILES_DIRS.append(os.path.join(BASE_DIR, 'sigir21_chatnoir_web', 'static'))
TEMPLATES[0]['DIRS'] = [
    os.path.join(BASE_DIR, 'ir_anthology_web', 'templates'),
    os.path.join(BASE_DIR, 'chatnoir', 'templates')
]

try:
   from .local_settings import *
except ImportError:
    raise RuntimeError("Could not find local_settings.py.")
