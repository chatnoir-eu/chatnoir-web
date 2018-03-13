from django import forms


class KeyRequestForm(forms.Form):
    commonname = forms.CharField(label='Name or organization', max_length=100,
                                 widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(label='Email address*', max_length=200,
                             widget=forms.EmailInput(attrs={'class': 'form-control'}))
    address = forms.CharField(label='Postal address', required=False,
                              widget=forms.TextInput(attrs={'class': 'form-control'}))
    zip_code = forms.CharField(label='ZIP code', required=False,
                               widget=forms.TextInput(attrs={'class': 'form-control'}))
    state = forms.CharField(label='State', required=False,
                            widget=forms.TextInput(attrs={'class': 'form-control'}))
    country = forms.CharField(label='Country', required=False,
                              widget=forms.TextInput(attrs={'class': 'form-control'}))
    passcode = forms.CharField(label='Passcode', max_length=100,
                               widget=forms.TextInput(attrs={'class': 'form-control'}))
    tos_accepted = forms.BooleanField(label='TOS accepted',
                                      widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
