from urllib import parse

from django import forms
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError


class TakedownForm(forms.Form):
    urls = forms.CharField(
        label='Cache URLs to take down',
        widget=forms.Textarea(attrs={'rows': 30, 'cols': 120}),
        help_text='Enter one cache URL per line (with index and UUID). Empty lines are ignored. Prefix with - to undo takedown.',
        required=False,
    )
    warc_target_uri_prefixes = forms.CharField(
        label='WARC target URI prefixes to take down',
        widget=forms.Textarea(attrs={'rows': 12, 'cols': 120}),
        help_text='Enter one URI prefix per line. The prefix is matched against warc_target_uri across all configured indices.'
                  'Prefix with - to undo takedown.',
        required=False,
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
                continue

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

        return takedowns

    def clean_warc_target_uri_prefixes(self):
        validator = URLValidator()
        prefixes = {}
        invalid_prefixes = []

        for line in self.cleaned_data['warc_target_uri_prefixes'].splitlines():
            prefix = line.strip()
            if not prefix:
                continue

            prefix_stripped = prefix if not prefix.startswith('-') else prefix[1:]
            try:
                validator(prefix_stripped)
            except ValidationError:
                invalid_prefixes.append(prefix_stripped)
                continue

            if prefix_stripped not in prefixes:
                prefixes[prefix_stripped] = {
                    'prefix': prefix_stripped,
                    'takedown': not prefix.startswith('-'),
                }

        if invalid_prefixes:
            raise ValidationError(
                'Invalid URI prefix%s: %s' % (
                    '' if len(invalid_prefixes) == 1 else 'es',
                    ', '.join(invalid_prefixes[:5]) + (' …' if len(invalid_prefixes) > 5 else ''),
                )
            )

        return prefixes

    def clean(self):
        cleaned_data = super().clean()
        if self.errors:
            return cleaned_data

        if not cleaned_data.get('urls') and not cleaned_data.get('warc_target_uri_prefixes'):
            raise ValidationError('Please provide at least one cache URL or WARC target URI prefix.')

        return cleaned_data
