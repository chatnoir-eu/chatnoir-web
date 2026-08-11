from urllib import parse

from django import forms
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError


class TakedownForm(forms.Form):
    urls = forms.CharField(
        label='Cache URLs to take down',
        widget=forms.Textarea(attrs={'rows': 30, 'cols': 120}),
        help_text='Enter one cache URL per line (with index and UUID). Empty lines are ignored. Prefix with - to undo takedown.',
    )

    def clean_urls(self):
        validator = URLValidator()
        takedowns = {}
        invalid_urls = []

        for line in self.cleaned_data['urls'].splitlines():
            url = line.strip()
            if not url:
                continue

            # Strip leading - before validation
            url_stripped = url if not url.startswith('-') else url[1:]
            try:
                validator(url_stripped)
            except ValidationError:
                invalid_urls.append(url_stripped)
                continue

            q = parse.parse_qs(parse.urlsplit(url_stripped).query)
            if not q.get('index') or not q.get('uuid'):
                invalid_urls.append(url_stripped)

            if url_stripped not in takedowns:
                takedowns[url_stripped] = {
                    'index': q['index'][0],
                    'uuid': q['uuid'][0],
                    'takedown': not url.startswith('-'),
                }

        if invalid_urls:
            raise ValidationError(
                'Invalid cache URL%s: %s' % (
                    '' if len(invalid_urls) == 1 else 's',
                    ', '.join(invalid_urls[:5]) + (' …' if len(invalid_urls) > 5 else ''),
                )
            )

        if not takedowns:
            raise ValidationError('Please provide at least one valid URL.')

        return takedowns
