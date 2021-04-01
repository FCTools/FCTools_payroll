# Copyright © 2020-2021 Filthy Claws Tools - All Rights Reserved
#
# This file is part of FCTools_payroll
#
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Author: German Yakimov <german13yakimov@gmail.com>

from django.db import models
from django.utils.html import format_html


class Test(models.Model):
    """
    This model represents Test.
    This object is formed from test budget, user, some traffic sources, some offers and geo (optional).

    The meaning of this object: this is the amount that an employee can spend free of charge
    on implementing these offers with these traffic sources and these geo.
    If the profit is negative, but is covered by the test budget,
    this negative profit is not deducted from the employee's salary.

    Note: each user has balance for each test. E.g. if test amount is 50$ and user profit is -20$,
    his balance for this test will be 30$.
    If user reaches a non-positive balance for some test (test amount spent), that test removes.
    """

    budget = models.DecimalField(verbose_name="Budget", null=False, blank=False, decimal_places=6, max_digits=13, )

    user = models.ForeignKey("User", on_delete=models.CASCADE, verbose_name="user", null=False, blank=False, )

    traffic_sources = models.ManyToManyField(
        "TrafficSource", verbose_name="Traffic sources", related_name="tests_list",
    )

    """
    If this flag set to True, than test budget will be split between all traffic sources.
    If this flag is False (as default), you need to "split" this test in django admin interface. Split action creates 
    test object for each traffic source, then it removes this object. 
    If system finds test with more than 1 traffic source and this flag set to False, it raises TestNotSplitError.
    """
    one_budget_for_all_traffic_sources = models.BooleanField(
        verbose_name="One budget for all traffic sources", default=False,
    )

    offers = models.ManyToManyField("Offer", verbose_name="Offers", related_name="tests_list", )

    one_budget_for_all_offers = models.BooleanField(
        verbose_name="One budget for all offers", default=False,
    )

    traffic_group = models.CharField(
        max_length=64,
        verbose_name="Traffic group",
        null=False,
        blank=False,
        choices=(
            ("ADMIN", "ADMIN"),
            ("FPA/HSA/PWA", "FPA/HSA/PWA"),
            ("INAPP traff", "INAPP traff"),
            ("NATIVE traff", "NATIVE traff"),
            ("POP traff", "POP traff"),
            ("PUSH traff", "PUSH traff"),
            ("Tik Tok", "Tik Tok"),
        ),
        default="PUSH traff",
    )

    balance = models.DecimalField(verbose_name="Balance", blank=False, null=False, decimal_places=6, max_digits=13, )

    geo = models.ManyToManyField("Geo", verbose_name="GEO", blank=True, )

    """
    If this flag set to True, than test budget will be split between all countries.
    If this flag is False (as default), you need to "split" this test in django admin interface. Split action creates 
    test object for each geo, then it removes this object. 
    If system finds test with more than 1 geo and this flag set to False, it raises TestNotSplitError.
    """
    one_budget_for_all_geo = models.BooleanField(verbose_name="One budget for all geo", default=False)

    adding_date = models.DateField(auto_now_add=True, verbose_name="Adding date", null=False, blank=False, )

    lifetime = models.PositiveIntegerField(verbose_name="Test lifetime (days)", default=60, null=False, blank=False, )

    archived = models.BooleanField(verbose_name="Archived", null=False, blank=False, default=False, )

    def budget_rounded(self):
        return round(self.budget, 4)

    budget_rounded.short_description = "Budget"

    def balance_colored(self):
        return format_html(
            f'<span style="color: {"#008000" if self.balance >= 0 else "#FF0000"};">' f"{round(self.balance, 4)}</span>"
        )

    balance_colored.short_description = "Balance"

    def offers_str(self):
        return " ||| ".join(sorted([str(offer) for offer in self.offers.all()]))

    offers_str.short_description = "Offers"

    def traffic_sources_str(self):
        return " ||| ".join(sorted([str(ts) for ts in self.traffic_sources.all()]))

    traffic_sources_str.short_description = "Traffic sources"

    def geo_str(self):
        return " ||| ".join(sorted([str(geo.iso_code) for geo in self.geo.all()]))

    geo_str.short_description = "GEO"

    def __str__(self):
        return f"{self.user} {self.offers_str()} {self.budget}"
