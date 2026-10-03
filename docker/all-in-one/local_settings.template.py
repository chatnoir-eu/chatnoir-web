"""
Default local_settings.py for the ChatNoir all-in-one Docker image.

This configuration points ChatNoir at the Elasticsearch and MinIO (S3) services
that are bundled and started inside the same container. It is meant for quick
local testing/demo purposes only. Mount your own local_settings.py over
/opt/chatnoir-web/chatnoir/chatnoir/local_settings.py for production use.
"""

import os

SECRET_KEY = os.environ.get('CHATNOIR_SECRET_KEY', 'RANDOM STRING - CHANGE ME')

DEBUG = os.environ.get('CHATNOIR_DEBUG', 'true').lower() in ('1', 'true', 'yes')
CSRF_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_SECURE = not DEBUG

if DEBUG:
    CORS_ALLOWED_ORIGINS = ['http://localhost:8000', 'http://127.0.0.1:8000']
    CSRF_TRUSTED_ORIGINS = CORS_ALLOWED_ORIGINS

# Configure email backend
EMAIL_HOST = 'localhost'
SERVER_EMAIL = 'no-reply@localhost'

# Configure database backend here (SQLite is fine for this all-in-one demo image)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': '/opt/chatnoir-web/db.sqlite3',
    }
}

# Elasticsearch runs inside this same container with security disabled, so no
# credentials are needed to connect to it.
ELASTICSEARCH_PROPERTIES = {
    'hosts': ['http://127.0.0.1:9200'],
    'retry_on_timeout': True,
    'timeout': 30,
}

# MinIO runs inside this same container. The root credentials below are fixed
# defaults baked into the image purely so that no manual S3 credential setup
# is required out of the box. Override MINIO_ROOT_USER/MINIO_ROOT_PASSWORD and
# this file (via a volume mount) if you need different/secret credentials.
S3_ENDPOINT_PROPERTIES = {
    'endpoint_url': 'http://127.0.0.1:9000',
    'aws_access_key_id': os.environ.get('MINIO_ROOT_USER', 'chatnoir'),
    'aws_secret_access_key': os.environ.get('MINIO_ROOT_PASSWORD', 'chatnoirchatnoir'),
}

# Configure search indices here. Add your own indices/buckets once you have
# ingested data into the bundled Elasticsearch/MinIO instances.
SEARCH_INDICES = {
    'cranfield': {
        'index': 'chatnoir_data_cranfield',
        'warc_index': 'chatnoir_meta_cranfield',
        'warc_bucket': 'corpora-tirex-small',
        'warc_uuid_prefix': 'cranfield',
        'display_name': 'Cranfield (demo)',
        'source_url': 'https://ir-datasets.com/cranfield.html',
        'compat_search_versions': [1],
        'default': True
    }
}

# Frontend URLs
SEARCH_FRONTEND_URL = 'http://127.0.0.1:8000/'
CACHE_FRONTEND_URL = 'http://127.0.0.1:8001/'
