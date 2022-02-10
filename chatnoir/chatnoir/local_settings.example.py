SECRET_KEY = 'RANDOM STRING'

DEBUG = True

# Configure email backend
EMAIL_HOST = 'localhost'
EMAIL_SENDER_ADDRESS = 'no-reply@localhost'
APIKEY_REQUEST_NOTIFY_EMAIL = 'janek.bevendorff@uni-weimar.de'

# Configure managers to receive notifications about pending API requests
MANAGERS = [
    ('John', 'john@localhost')
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
