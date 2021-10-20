import json

from django import template
from django.conf import settings


register = template.Library()


@register.filter(name='json')
def json_filter(value):
    return json.dumps(value)


@register.simple_tag
def app_name():
    return settings.APPLICATION_NAME
