SECRET_KEY = 'RANDOM STRING'

DEBUG = False

if DEBUG:
    CORS_ALLOW_ALL_ORIGINS = True
    CSRF_TRUSTED_ORIGINS = [
        'localhost:8080',
        '127.0.0.1:8080'
    ]

# Configure database backend here
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'db.sqlite3',
    }
}

# Configure Elasticsearch backend here
ELASTICSEARCH_PROPERTIES = {
    'hosts': ['ELASTICSEARCH_HOST:PORT'],
    'retry_on_timeout': True,
    'use_ssl': True,
    'api_key': ['API_KEY_NAME', 'API_KEY_SECRET'],
    'timeout': 30
}

# Configure S3 backend here
S3_ENDPOINT_PROPERTIES = {
    "endpoint_url": "http://localhost",
    "aws_access_key_id": "access_key",
    "aws_secret_access_key": "secret_key"
}

# Configure search indices here
SEARCH_INDICES = {
  'INDEX_SHORTHAND': {
      'index': 'INDEX_NAME',
      'warc_index': '',
      'warc_bucket': '',
      'warc_uuid_prefix': '',
      'display_name': '',
      'compat_search_versions': [1],
      'default': True
  }
}
