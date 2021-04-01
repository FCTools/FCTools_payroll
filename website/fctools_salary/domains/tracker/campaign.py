# Copyright © 2020-2021 Filthy Claws Tools - All Rights Reserved
#
# This file is part of FCTools_payroll
#
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Author: German Yakimov <german13yakimov@gmail.com>

from django.conf import settings
from django.db import models
from django.utils.html import format_html


class Campaign(models.Model):
    """
    This model represents campaign from tracker (http://fcttrk.com/?page=Campaigns).
    In addition, there is offers_list - many to many field to Offer model.
    """

    id = models.IntegerField(primary_key=True, verbose_name="ID", unique=True, blank=False, null=False, )

    name = models.CharField(max_length=256, verbose_name="Name", null=True, blank=True, )

    traffic_group = models.CharField(
        max_length=16,
        verbose_name="Traffic group",
        null=False,
        blank=False,
        choices=settings.TRAFFIC_GROUPS,
    )

    traffic_source = models.ForeignKey(
        "TrafficSource", on_delete=models.CASCADE, verbose_name="Traffic source", blank=False, null=False,
    )

    revenue = models.DecimalField(verbose_name="Revenue", null=False, blank=False, decimal_places=6, max_digits=12, )

    cost = models.DecimalField(verbose_name="Cost", null=False, blank=False, decimal_places=6, max_digits=12, )

    profit = models.DecimalField(verbose_name="Profit", null=False, blank=False, decimal_places=6, max_digits=12, )

    user = models.ForeignKey("User", verbose_name="User", on_delete=models.CASCADE, null=True, blank=False, )

    offers_list = models.ManyToManyField("Offer", related_name="campaigns_list", verbose_name="Offers", )

    def profit_colored(self):
        if self.profit < 0:
            color_code = "#FF0000"  # negative profit - red color
        elif self.profit > 0:
            color_code = "#008000"  # positive profit - green color
        else:
            color_code = "#D3D3D3"  # null profit - grey color

        return format_html(f'<span style="color: {color_code};">{round(self.profit, 4)}</span>')

    profit_colored.short_description = "Profit"

    def cost_rounded(self):
        return round(self.cost, 4)

    cost_rounded.short_description = "Cost"

    def revenue_rounded(self):
        return round(self.revenue, 4)

    revenue_rounded.short_description = "Revenue"

    def __str__(self):
        return f"{self.id} {self.name}"

    def __eq__(self, other):
        if not other:
            return False

        return all(
            [
                self.id == other.id,
                self.name == other.name,
                self.traffic_group == other.traffic_group,
                self.traffic_source == other.traffic_source,
            ]
        )

    def __hash__(self):
        return hash((self.id, self.name, self.traffic_source))
