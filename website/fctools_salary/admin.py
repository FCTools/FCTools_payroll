"""
Copyright © 2020 FC Tools. All rights reserved.
Author: German Yakimov
"""

from datetime import datetime, timedelta

from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError

from fctools_salary.domains.accounts.percent_dependency import PercentDependency
from fctools_salary.domains.accounts.report import Report
from fctools_salary.domains.accounts.test import Test
from fctools_salary.domains.accounts.user import User
from fctools_salary.domains.tracker.campaign import Campaign
from fctools_salary.domains.tracker.geo import Geo
from fctools_salary.domains.tracker.offer import Offer
from fctools_salary.domains.tracker.traffic_source import TrafficSource
from fctools_salary.services.helpers.test_splitter import TestSplitter
from fctools_salary.filters import ActiveUsersFilter


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "login",
        "is_lead",
        "salary_group",
    ]

    list_display_links = [
        "id",
        "login",
    ]

    list_filter = [
        "is_lead",
        "salary_group",
    ]

    search_fields = [
        "login",
        "id",
    ]


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "name",
        "geo",
        "group",
        "network",
    ]

    list_display_links = [
        "id",
        "name",
    ]

    list_filter = [
        "geo",
        "group",
        "network",
    ]

    search_fields = [
        "name",
        "id",
    ]


@admin.register(TrafficSource)
class TrafficSourceAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "name",
        "user",
    ]

    list_display_links = [
        "id",
        "name",
    ]

    list_filter = [
        ActiveUsersFilter,
    ]

    list_select_related = [
        "user",
    ]

    search_fields = [
        "name",
        "id",
    ]


class TestForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(TestForm, self).__init__(*args, **kwargs)
        self.fields["user"].queryset = User.objects.filter(salary_group__gt=0)
        self.fields["traffic_sources"].queryset = TrafficSource.objects.select_related("user").filter(
            user__salary_group__gt=0
        )

    class Meta:
        model = Test
        fields = [
            "budget",
            "user",
            "offers",
            "one_budget_for_all_offers",
            "traffic_sources",
            "one_budget_for_all_traffic_sources",
            "traffic_group",
            "balance",
            "geo",
            "one_budget_for_all_geo",
            "lifetime",
            "archived",
        ]

    def clean_traffic_sources(self):
        traffic_sources_list = self.cleaned_data["traffic_sources"]

        for traffic_source in traffic_sources_list.all():
            if traffic_source.user_id != self.cleaned_data["user"].id:
                raise ValidationError(f"Traffic source [{traffic_source}] pinned to another user.")

        return traffic_sources_list

    def clean_budget(self):
        amount = self.cleaned_data["budget"]

        if amount <= 0:
            raise ValidationError("Test budget must be positive.")

        return amount

    def clean_balance(self):
        balance = self.cleaned_data["balance"]

        if "budget" in self.cleaned_data:
            budget = self.cleaned_data["budget"]
        else:
            return balance

        if balance <= 0:
            raise ValidationError("Test balance must be positive")
        elif balance > budget:
            raise ValidationError("Test balance can't be greater than test budget.")
        else:
            return balance

    def clean(self):
        if "traffic_sources" in self.cleaned_data:
            traffic_sources_list = self.cleaned_data["traffic_sources"].all()
        else:
            super(TestForm, self).clean()
            return

        if not self.instance.id:
            related_tests = Test.objects.filter(
                user=self.cleaned_data["user"], traffic_group=self.cleaned_data["traffic_group"]
            )
            offers_list = " ||| ".join(sorted([str(offer) for offer in self.cleaned_data["offers"].all()]))
            ts_list = " ||| ".join(sorted([str(ts) for ts in traffic_sources_list]))
            geo_list = " ||| ".join(sorted([str(geo.iso_code) for geo in self.cleaned_data["geo"].all()]))

            for test in related_tests:
                if (
                        test.offers_str() == offers_list
                        and test.traffic_sources_str() == ts_list
                        and geo_list == test.geo_str()
                ):
                    raise ValidationError("This test already exists.")

        super(TestForm, self).clean()


def split_tests(modeladmin, request, queryset):
    splitter = TestSplitter()

    for test in queryset:
        splitter.split(test)


split_tests.short_description = "Split selected tests"


def archive_expired_tests(modeladmin, request, queryset):
    today = datetime.utcnow().date()

    for test in queryset:
        if today - test.adding_date >= timedelta(days=test.lifetime):
            test.archived = True
            test.save()


archive_expired_tests.short_description = "Archive expired tests"


@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "offers_str",
        "user",
        "traffic_sources_str",
        "traffic_group",
        "budget_rounded",
        "balance_colored",
        "geo_str",
        "adding_date",
        "lifetime",
        "archived",
    ]

    list_filter = [
        "traffic_group",
        "archived",
        ActiveUsersFilter,
    ]

    list_select_related = [
        "user",
    ]

    form = TestForm

    filter_horizontal = [
        "offers",
        "traffic_sources",
        "geo",
    ]

    list_display_links = [
        "id",
        "offers_str",
    ]

    actions = [split_tests, archive_expired_tests, ]

    search_fields = ['offers__id',
                     'user__login',
                     'traffic_sources__id',
                     'traffic_sources__name',
                     'offers__name', ]


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "name",
        "traffic_group",
        "traffic_source",
        "cost_rounded",
        "revenue_rounded",
        "profit_colored",
        "user",
    ]

    list_display_links = [
        "id",
        "name",
    ]

    list_filter = [
        "traffic_group",
        ActiveUsersFilter,
    ]

    list_select_related = [
        "traffic_source",
    ]

    search_fields = [
        "traffic_source__name",
        "id",
        "offers_list__id",
        "user__login",
    ]


@admin.register(PercentDependency)
class PercentDependencyAdmin(admin.ModelAdmin):
    list_display = [
        "from_user",
        "to_user",
        "percent",
    ]

    list_filter = [
        "from_user",
        "to_user",
    ]

    list_select_related = [
        "from_user",
        "to_user",
    ]


@admin.register(Geo)
class GeoAdmin(admin.ModelAdmin):
    list_display = [
        "country",
        "iso_code",
    ]

    list_display_links = [
        "country",
        "iso_code",
    ]


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "start_date",
        "end_date",
        "profit_admin",
        "profit_push",
        "profit_pop",
        "profit_native",
        "profit_inapp",
        "profit_fpa_hsa_pwa",
        "profit_tik_tok",
        "percent_admin",
        "percent_push",
        "percent_pop",
        "percent_native",
        "percent_inapp",
        "percent_fpa_hsa_pwa",
        "percent_tik_tok",
    ]
