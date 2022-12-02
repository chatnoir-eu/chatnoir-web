"""
Django admin UI proxy app for ChatNoir.

This is a proxy settings module that allows running the admin backend as a standalone
app for deployment behind a firewall instead of the public web.

The actual Django app settings to load are specified via the `CHATNOIR_SETTINGS_MODULE`
environment variable. The proxy module will override `ROOT_URLCONF` with its own routes.
"""

import importlib
import os

__settings = importlib.import_module(os.getenv('CHATNOIR_SETTINGS_MODULE', 'chatnoir.settings'))

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INSTALLED_APPS = []
TEMPLATES = []

for attr in dir(__settings):
    globals()[attr] = getattr(__settings, attr)

ROOT_URLCONF = 'chatnoir_admin.urls'
if 'django.contrib.admin' not in INSTALLED_APPS:
    INSTALLED_APPS.append('django.contrib.admin')

TEMPLATES[0]['DIRS'].append(os.path.join(BASE_DIR, 'chatnoir_admin', 'templates'))
