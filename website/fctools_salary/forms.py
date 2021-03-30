"""
Copyright © 2020-2021 FC Tools.
All rights reserved.
Author: German Yakimov
"""

from django import forms
from django.conf import settings
from tempus_dominus.widgets import DatePicker

from fctools_salary.domains.accounts.user import User


class CalculationForm(forms.Form):
    """
    This form created for calculation configuration on /count page. Here you can select user,
    period and other parameters.
    """

    user = forms.ModelChoiceField(
        queryset=User.objects.filter(salary_group__gt=0), required=True, widget=forms.Select(attrs={"class": "field"})
    )

    update_db = forms.BooleanField(initial=False, required=False)

    traffic_groups = forms.MultipleChoiceField(
        choices=settings.TRAFFIC_GROUPS,
        widget=forms.SelectMultiple,
        required=True,
    )

    start_date = forms.DateField(
        required=True, widget=DatePicker(attrs={"append": "fa fa-calendar", "icon_toggle": True, })
    )

    end_date = forms.DateField(
        required=True, widget=DatePicker(attrs={"append": "fa fa-calendar", "icon_toggle": True, })
    )

    cost = forms.FloatField(required=False, min_value=0, max_value=100000., initial=None)

    def clean(self):
        return self.cleaned_data
