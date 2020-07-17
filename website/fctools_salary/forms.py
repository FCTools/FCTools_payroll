from django import forms
from tempus_dominus.widgets import DatePicker

from fctools_salary.domains.accounts.user import User


class ReportInfoForm(forms.Form):
    """
    This form created for calculation configuration on /count page. Here you can select user,
    period and other parameters.
    """

    user = forms.ModelChoiceField(
        queryset=User.objects.filter(salary_group__gt=0), required=True, widget=forms.Select(attrs={"class": "field"})
    )

    update_db = forms.BooleanField(initial=False, required=False)

    traffic_groups = forms.MultipleChoiceField(
        choices=(
            ("ADMIN", "ADMIN"),
            ("FPA/HSA/PWA", "FPA/HSA/PWA"),
            ("INAPP traff", "INAPP traff"),
            ("NATIVE traff", "NATIVE traff"),
            ("POP traff", "POP traff"),
            ("PUSH traff", "PUSH traff"),
        ),
        widget=forms.SelectMultiple,
        required=True,
    )

    start_date = forms.DateField(
        required=True, widget=DatePicker(attrs={"append": "fa fa-calendar", "icon_toggle": True,})
    )

    end_date = forms.DateField(
        required=True, widget=DatePicker(attrs={"append": "fa fa-calendar", "icon_toggle": True,})
    )

    def clean(self):
        return self.cleaned_data
