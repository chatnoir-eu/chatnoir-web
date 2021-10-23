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

# Configure search indices here
SEARCH_INDEXES = {
  'INDEX_SHORTHAND': {
      'index': 'INDEX_NAME',
      'warc_index': '',
      'warc_bucket': '',
      'warc_uuid_prefix': '',
      'display_name': '',
      'compat_search_versions': [1]
  }
}
SEARCH_DEFAULT_INDEXES = {
  1: 'INDEX_SHORTHAND'
}
