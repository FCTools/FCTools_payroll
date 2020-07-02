from django import forms
from tempus_dominus.widgets import DatePicker

from .models import User


class ReportInfoForm(forms.Form):
    user = forms.ModelChoiceField(queryset=User.objects.filter(group__gt=0), required=True, widget=forms.Select(attrs={
        'class': 'field'}))
    update_db = forms.BooleanField(initial=False, required=False)
    start_date = forms.DateField(required=True, widget=DatePicker(
        attrs={
            'append': 'fa fa-calendar',
            'icon_toggle': True,
        }
    ))

    end_date = forms.DateField(required=True, widget=DatePicker(
        attrs={
            'append': 'fa fa-calendar',
            'icon_toggle': True,
        }
    ))

    def clean(self):
        return self.cleaned_data
