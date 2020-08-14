from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Passcode, PendingUser, User


class KeyRequestForm(forms.ModelForm):
    class Meta:
        model = PendingUser
        fields = [
            'commonname',
            'email',
            'organization',
            'address',
            'zip_code',
            'state',
            'country',
            'passcode'

        ]
        widgets = {
            'commonname': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'organization': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'zip_code': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
            'passcode': forms.TextInput(attrs={'class': 'form-control'})
        }

    tos_accepted = forms.BooleanField(widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))

    def clean(self):
        cleaned_data = super().clean()
        self._validate_unique = False

        try:
            pc = Passcode.objects.get(passcode=self.data.get('passcode', ''))
            cleaned_data['passcode'] = pc
            del self._errors['passcode']

            # check if API key for this email address / passcode combination has already been issued
            existing_user = User.objects.filter(passcode=pc, email_address=cleaned_data.get('email', 'xx')).count()
            if existing_user > 0:
                self._errors['passcode'] = self.error_class([
                    _('Passcode already redeemed.')])
        except Passcode.DoesNotExist:
            self._errors['passcode'] = self.error_class([_('The passcode "{0}" is invalid.').format(
                self.data.get('passcode', ''))])

        return cleaned_data

    def update_instance(self, instance, activation_code):
        instance.activation_code = activation_code
        instance.address = self.cleaned_data.get('address', '')
        instance.zip_code = self.cleaned_data.get('zip_code', '')
        instance.zip_code = self.cleaned_data.get('zip_code', '')
        instance.state = self.cleaned_data.get('state', '')
        instance.country = self.cleaned_data.get('country', '')
        instance.save()
