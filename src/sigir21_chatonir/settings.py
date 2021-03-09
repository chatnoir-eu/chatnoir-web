"""
Django settings for ChatonIR.
"""

from chatnoir.settings import *

APPLICATION_NAME = 'ChatonIR Anthology Search'

INSTALLED_APPS.append('sigir21_chatonir_web.apps.ChatonIRWebConfig')

ROOT_URLCONF = 'sigir21_chatonir.urls'
# STATICFILES_DIRS.append(os.path.join(BASE_DIR, 'sigir21_chatnoir_web', 'static'))
TEMPLATES[0]['DIRS'] = [
    os.path.join(BASE_DIR, 'sigir21_chatonir_web', 'templates'),
    os.path.join(BASE_DIR, 'chatnoir', 'templates')
]

try:
   from .local_settings import *
except ImportError:
    raise RuntimeError("Could not find local_settings.py.")
