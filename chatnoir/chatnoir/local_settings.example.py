SECRET_KEY = 'RANDOM STRING'

DEBUG = True

# Allow cross-site requests from dev web frontend for debugging purposes
if DEBUG:
    CORS_ALLOWED_ORIGINS = ['http://localhost:5173', 'http://127.0.0.1:5173']
    CSRF_TRUSTED_ORIGINS = CORS_ALLOWED_ORIGINS

# Configure email backend
EMAIL_HOST = 'localhost'
SERVER_EMAIL = 'no-reply@localhost'

# Configure managers to receive notifications about pending API requests
MANAGERS = [
    ('Jane Doe', 'jane.doe@example.com')
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
  'index_shorthand': {                  # Index shorthand for referencing it in ChatNoir
      'index': '',                      # Elasticsearch index name
      'warc_index': '',                 # Elasticsearch WARC offset index
      'warc_bucket': '',                # WARC S3 bucket
      'warc_uuid_prefix': '',           # WARC document UUID prefix
      'display_name': '',               # Friendly index name
      'source_url': '',                 # URL to upstream source dataset
      'compat_search_versions': [1],    # Compatible search versions (so far always 1)
      'default': True                   # Whether this is the default index (optional)
  }
}

# Frontend URLs
SEARCH_FRONTEND_URL = 'http://127.0.0.1:8000/'
CACHE_FRONTEND_URL = 'http://127.0.0.1:8001/'
