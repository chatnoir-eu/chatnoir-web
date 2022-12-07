# Copyright 2021 Janek Bevendorff
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from .models import ApiConfiguration, ApiKeyPasscode, ApiPendingUser, PasscodeRedemption


class KeyRequestForm(forms.ModelForm):
    class Meta:
        model = ApiPendingUser
        fields = [
            'common_name',
            'email',
            'organization',
            'address',
            'zip_code',
            'state',
            'country',
            'passcode',
            'comments'
        ]

    tos_accepted = forms.BooleanField(required=True)
    privacy_accepted = forms.BooleanField(required=True)

    def __init__(self, *args, passcode=True, **kwargs):
        super().__init__(*args, **kwargs)
        self.passcode = passcode
        if not self.data.get('passcode'):
            self.fields['organization'].required = True
            self.fields['comments'].required = True

    def save(self, commit=True):
        if not self.instance.passcode:
            self.instance.issue_key = ApiConfiguration.objects.get().default_issue_key
        return super().save(commit)

    def clean(self):
        cleaned_data = super().clean()

        if 'passcode' in self._errors:
            # The default passcode field validation is useless, we'll deal with this later
            del self._errors['passcode']

        if self.passcode:
            cleaned_data['passcode'] = self.data.get('passcode', '').strip()
            if not cleaned_data.get('passcode'):
                self.add_error('passcode', ValidationError(_('A valid passcode is required.'), 'required'))
                return

            try:
                pc = ApiKeyPasscode.objects.get(Q(passcode=cleaned_data.get('passcode')),
                                                Q(expires__isnull=True) | Q(expires__gt=timezone.now()))
                cleaned_data['passcode'] = pc

                # check if API key for this email address / passcode combination has already been issued
                redeemed = PasscodeRedemption.objects.filter(passcode=pc,
                                                             api_key__user__email=cleaned_data['email']).exists()
                if not redeemed:
                    redeemed = ApiPendingUser.objects.filter(passcode=pc, email=cleaned_data['email']).exists()

                if redeemed:
                    self.add_error('passcode', ValidationError(_('Passcode already redeemed.'), 'already-redeemed'))
            except ApiKeyPasscode.DoesNotExist:
                self.add_error('passcode', ValidationError(
                    _('The passcode "{}" is invalid.').format(cleaned_data.get('passcode', '')), 'invalid'))

            try:
                if cleaned_data.get('passcode'):
                    ApiPendingUser.objects.get(email=cleaned_data['email'], passcode=cleaned_data['passcode'])
                    self.add_error(
                        'email', ValidationError(_('API key request for user already submitted.'), 'duplicate'))
            except ApiPendingUser.DoesNotExist:
                pass

        else:
            try:
                ApiPendingUser.objects.get(email=cleaned_data['email'])
                self.add_error('email', ValidationError(_('API key request for user already submitted.'), 'duplicate'))
            except ApiPendingUser.DoesNotExist:
                pass

            if not cleaned_data.get('organization'):
                self.add_error('organization', ValidationError(_('Your academic institute is required.'), 'required'))
            if not cleaned_data.get('comments'):
                self.add_error('comments', ValidationError(_('Please describe your use case.'), 'required'))

        return cleaned_data


class PendingApiUserAdminForm(forms.ModelForm):
    class Meta:
        model = ApiPendingUser
        exclude = []

    activate_user = forms.BooleanField(label=_('Activate user and notify by email'), required=False)
    deny_request = forms.ChoiceField(label=_('Deny request with reason:'), required=False, choices=(
        ('', ''),
        ('academic-status', _('Could not verify academic affiliation')),
        ('already-issued', _('API key already issued to user')),
        ('applications-suspended', _('New applications temporarily suspended'))
    ))
    confirm_denial = forms.BooleanField(label=_('Confirm denial'), required=False)

    def clean(self):
        if self.cleaned_data.get('activate_user') and (
                self.cleaned_data.get('deny_request') or self.cleaned_data.get('confirm_denial')):
            self.add_error('activate_user', _('Cannot approve and deny request at the same time'))
        elif self.cleaned_data.get('deny_request') and not self.cleaned_data.get('confirm_denial'):
            self.add_error('confirm_denial', _('Check to confirm API key request denial'))
        elif self.cleaned_data.get('confirm_denial') and not self.cleaned_data.get('deny_request'):
            self.add_error('confirm_denial', _('You must select a reason'))

        if self.cleaned_data.get('activate_user') and not \
                self.cleaned_data.get('issue_key') and not self.cleaned_data.get('passcode'):
            self.add_error('issue_key', _('API user must be assigned either an issue key or a passcode.'))

        return super().clean()
