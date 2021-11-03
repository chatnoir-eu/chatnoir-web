import json
from time import time

from django import template
from django.conf import settings
from django.middleware.csrf import get_token, CSRF_SESSION_KEY
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter(name='json')
def json_filter(value):
    return json.dumps(value)


@register.simple_tag
def app_name():
    return settings.APPLICATION_NAME


@register.simple_tag(takes_context=True)
def search_request_token(context):
    """
    Get time-limited CSRF token as JSON with timestamps.
    A side-effect of this template tag is that it refreshes the lifetime of the current token.
    """
    ts = time()
    context['request'].session[CSRF_SESSION_KEY + '_TIME'] = ts

    return mark_safe(json.dumps(dict(
        token=get_token(context['request']),
        timestamp=int(ts),
        max_age=settings.CSRF_MAX_TOKEN_AGE)))
