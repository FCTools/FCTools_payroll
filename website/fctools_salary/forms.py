from django import forms
from django.contrib.auth import authenticate

from .models import User


class LoginForm(forms.Form):
    login = forms.CharField(label='Login', required=True, widget=forms.TextInput(attrs={'class': 'field_login'}))
    password = forms.CharField(label='Password', widget=forms.PasswordInput(attrs={'class': 'field_password'}),
                               required=True)

    def clean(self):
        login = self.cleaned_data['login']
        password = self.cleaned_data['password']

        user = authenticate(username=login, password=password)

        if user is not None:
            return self.cleaned_data
        else:
            raise forms.ValidationError('Incorrect login data')


class ReportInfoForm(forms.Form):
    user = forms.ModelChoiceField(queryset=User.objects.all(), required=True)
    start_date = forms.DateField(required=True, widget=forms.DateInput(attrs={'class': 'field'}),
                                 input_formats=['%Y-%m-%d'])
    end_date = forms.DateField(required=True, widget=forms.DateInput(attrs={'class': 'field'}),
                               input_formats=['%Y-%m-%d'])

    def clean(self):
        return self.cleaned_data
