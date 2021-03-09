from html import escape as html_escape
from urllib.parse import quote as url_quote

from django import template
from django.urls import reverse


register = template.Library()


@register.filter(name='author_list')
def author_list(authors, link_targets=False):
    authors = [a.split(' ')[-1] for a in authors]

    if link_targets:
        link_base = f'{reverse("search:index")}?q=author%3A'
        authors = [f'<a href="{link_base + url_quote(a.lower())}">{html_escape(a)}</a>' for a in authors]

    if 1 <= len(authors) <= 2:
        return ' and '.join(authors)
    elif len(authors) > 2:
        return f'{authors[0]} et al.'
    return 'unknown'
