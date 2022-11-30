import json
from time import time

from django import template
from django.conf import settings
from django.utils.safestring import mark_safe

from chatnoir_api_v1.authentication import ApiKeyAuthentication

register = template.Library()


@register.filter(name='json')
def json_filter(value):
    return json.dumps(value)


@register.simple_tag
def app_name():
    return settings.APPLICATION_NAME


@register.simple_tag(takes_context=True)
def search_session_apikey(context):
    """
    Get a temporary session API key.
    Using this template tag will invalidate any previous session API key.
    """
    apikey = ApiKeyAuthentication.issue_temporary_session_apikey(context['request'], issuer='web_frontend')
    return mark_safe(json.dumps(dict(
        token=apikey.api_key,
        timestamp=int(apikey.issue_date.timestamp()),
        max_age=int((apikey.expires - apikey.issue_date).total_seconds()) + 1)))
