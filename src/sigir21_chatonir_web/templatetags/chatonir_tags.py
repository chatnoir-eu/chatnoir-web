from html import escape as html_escape
from urllib.parse import quote as url_quote

from django import template
from django.urls import reverse


register = template.Library()


@register.filter(name='author_list')
def author_list(authors, link_targets=False):
    authors_last = [a.split(' ')[-1] for a in authors]

    if link_targets:
        link_base = f'{reverse("search:index")}?q=author%3A'
        authors_last = [
            f'<a href="{"".join((link_base, "%22", url_quote(authors[i].lower()), "%22"))}">{html_escape(al)}</a>'
            for i, al in enumerate(authors_last)]

    if 1 <= len(authors_last) <= 2:
        return ' and '.join(authors_last)
    elif len(authors_last) > 2:
        return f'{authors_last[0]} et al.'
    return 'unknown'
