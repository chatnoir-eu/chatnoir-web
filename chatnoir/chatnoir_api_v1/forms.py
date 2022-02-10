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
from django.utils.translation import gettext_lazy as _

from .models import ApiKeyPasscode, PendingApiUser, PasscodeRedemption


class KeyRequestForm(forms.ModelForm):
    class Meta:
        model = PendingApiUser
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
    organization = forms.CharField(required=True)

    def __init__(self, *args, passcode=True, **kwargs):
        super().__init__(*args, **kwargs)
        self.passcode = passcode
        if not self.data.get('passcode'):
            self.fields['organization'].required = True
            self.fields['comments'].required = True

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
                pc = ApiKeyPasscode.objects.get(passcode=cleaned_data.get('passcode'))
                cleaned_data['passcode'] = pc

                # check if API key for this email address / passcode combination has already been issued
                redeemed = PasscodeRedemption.objects.filter(passcode=pc,
                                                             api_key__user__email=cleaned_data.get('email')).exists()
                if not redeemed:
                    redeemed = PendingApiUser.objects.filter(passcode=pc, email=cleaned_data.get('email')).exists()

                if redeemed:
                    self.add_error('passcode', ValidationError(_('Passcode already redeemed.'), 'already-redeemed'))
            except ApiKeyPasscode.DoesNotExist:
                self.add_error('passcode', ValidationError(
                    _('The passcode "{}" is invalid.').format(cleaned_data.get('passcode', '')), 'invalid'))
        else:
            if not cleaned_data.get('organization'):
                self.add_error('organization', ValidationError(_('Your academic institute is required.'), 'required'))
            if not cleaned_data.get('comments'):
                self.add_error('comments', ValidationError(_('Please describe your use case.'), 'required'))

        return cleaned_data
