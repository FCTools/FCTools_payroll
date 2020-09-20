"""
Copyright © 2020 FC Tools. All rights reserved.
Author: German Yakimov
"""
from datetime import datetime, timedelta

from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError

from fctools_salary.domains.accounts.percent_dependency import PercentDependency
from fctools_salary.domains.accounts.test import Test
from fctools_salary.domains.accounts.user import User
from fctools_salary.domains.accounts.report import Report
from fctools_salary.domains.tracker.campaign import Campaign
from fctools_salary.domains.tracker.geo import Geo
from fctools_salary.domains.tracker.offer import Offer
from fctools_salary.domains.tracker.traffic_source import TrafficSource


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
        "user",
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
            "traffic_sources",
            "traffic_group",
            "balance",
            "one_budget_for_all_traffic_sources",
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
    for test in queryset:
        test_offers = list(test.offers.all())
        test_traffic_sources = list(test.traffic_sources.all())
        test_geo = list(test.geo.all())

        if not test.one_budget_for_all_traffic_sources:
            for traffic_source in test_traffic_sources:
                new_test_ts = Test(
                    user=test.user,
                    budget=test.budget,
                    balance=test.balance,
                    traffic_group=test.traffic_group,
                    one_budget_for_all_geo=test.one_budget_for_all_geo,
                    adding_date=test.adding_date,
                    archived=test.archived,
                    lifetime=test.lifetime,
                )
                new_test_ts.save()

                new_test_ts.offers.add(*test_offers)
                new_test_ts.geo.add(*test_geo)
                new_test_ts.traffic_sources.add(traffic_source)
                new_test_ts.save()

                if not test.one_budget_for_all_geo and test_geo:
                    for geo in test_geo:
                        new_test_geo = Test(
                            user=test.user,
                            budget=test.budget,
                            balance=test.balance,
                            traffic_group=test.traffic_group,
                            adding_date=test.adding_date,
                            archived=test.archived,
                            lifetime=test.lifetime,
                        )
                        new_test_geo.save()
                        new_test_geo.offers.add(*test_offers)
                        new_test_geo.traffic_sources.add(traffic_source)
                        new_test_geo.geo.add(geo)
                        new_test_geo.save()
                    new_test_ts.delete()

            test.delete()

        elif not test.one_budget_for_all_geo:
            for geo in test_geo:
                new_test_geo = Test(
                    user=test.user,
                    budget=test.budget,
                    balance=test.balance,
                    traffic_group=test.traffic_group,
                    one_budget_for_all_traffic_sources=test.one_budget_for_all_traffic_sources,
                    adding_date=test.adding_date,
                    archived=test.archived,
                    lifetime=test.lifetime,
                )
                new_test_geo.save()
                new_test_geo.offers.add(*test_offers)
                new_test_geo.traffic_sources.add(*test_traffic_sources)
                new_test_geo.geo.add(geo)
                new_test_geo.save()
            test.delete()


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
        "user",
        "traffic_group",
        "archived",
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
        "traffic_source",
        "user",
    ]

    list_select_related = [
        "user",
        "traffic_source",
    ]

    search_fields = [
        "name",
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
    pass

