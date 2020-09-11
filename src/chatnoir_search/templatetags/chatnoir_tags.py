import json

from django import template


register = template.Library()


@register.filter(name='json')
def json_filter(value):
    return json.dumps(value)
