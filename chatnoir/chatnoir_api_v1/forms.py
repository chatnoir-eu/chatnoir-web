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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.data.get('passcode'):
            print('dsafdsf')
            self.fields['organization'].required = True
            self.fields['comments'].required = True

    def clean(self):

        # No passcode provided, assume academic key request
        # if not self.data.get('passcode'):
        #     print(dir(self.fields['comments']))
        #     self.fields['comments'].required = True
        #     self.fields['comments'].clean('')

        cleaned_data = super().clean()
        if cleaned_data.get('passcode'):
            try:
                pc = ApiKeyPasscode.objects.get(passcode=cleaned_data.get('passcode'))
                cleaned_data['passcode'] = pc
                del self._errors['passcode']

                # check if API key for this email address / passcode combination has already been issued
                redeemed = PasscodeRedemption.objects.filter(passcode=pc,
                                                             api_key__user__email=cleaned_data.get('email')).exists()
                if not redeemed:
                    redeemed = PendingApiUser.objects.filter(passcode=pc, email=cleaned_data.get('email')).exists()

                if redeemed:
                    self.add_error('passcode', _('Passcode already redeemed.'))
            except ApiKeyPasscode.DoesNotExist:

                self.add_error('passcode', _('The passcode "{}" is invalid.').format(self.data.get('passcode', '')))
        else:
            if not cleaned_data.get('organization'):
                self.add_error('organization', _('Your academic institute is required.'))
            if not cleaned_data.get('comments'):
                self.add_error('comments', _('Please describe your use case.'))

        return cleaned_data

    def update_instance(self, instance, activation_code):
        instance.activation_code = activation_code
        instance.address = self.cleaned_data.get('address', '')
        instance.zip_code = self.cleaned_data.get('zip_code', '')
        instance.zip_code = self.cleaned_data.get('zip_code', '')
        instance.state = self.cleaned_data.get('state', '')
        instance.country = self.cleaned_data.get('country', '')
        instance.save()
