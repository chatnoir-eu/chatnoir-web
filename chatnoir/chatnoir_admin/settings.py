"""
Django admin UI proxy app for ChatNoir.

This is a proxy settings module that allows running the admin backend as a standalone
app for deployment behind a firewall instead of the public web.

The actual Django app settings to load are specified via the `CHATNOIR_SETTINGS_MODULE`
environment variable. The proxy module will override `ROOT_URLCONF` with its own routes.
"""

import importlib
import os

if not os.getenv('CHATNOIR_SETTINGS_MODULE'):
    raise RuntimeError('CHATNOIR_SETTINGS_MODULE environment variable unset.')

__settings = importlib.import_module(os.getenv('CHATNOIR_SETTINGS_MODULE'))

INSTALLED_APPS = []

for attr in dir(__settings):
    globals()[attr] = getattr(__settings, attr)

ROOT_URLCONF = 'chatnoir_admin.urls'
if 'django.contrib.admin' not in INSTALLED_APPS:
    INSTALLED_APPS.append('django.contrib.admin')
