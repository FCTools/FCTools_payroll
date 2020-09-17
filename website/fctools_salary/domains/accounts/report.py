"""
Copyright 2020 FC Tools. All rights reserved.
Author: German Yakimov
"""

from django.db import models


class Report(models.Model):
    """
    This model represents salary report for period.
    """

    user = models.ForeignKey(to="User", verbose_name="User", null=False, blank=False, on_delete=models.DO_NOTHING, )

    start_date = models.DateField(verbose_name="Start date", null=False, blank=False, )

    end_date = models.DateField(verbose_name="End date", null=False, blank=False, )

    profit = models.DecimalField(verbose_name="Current profit", null=False, blank=False, decimal_places=6, max_digits=13, )

    cost = models.DecimalField(verbose_name="Current cost", null=False, blank=False, decimal_places=6, max_digits=13, )

    revenue = models.DecimalField(verbose_name="Current revenue", null=False, blank=False, decimal_places=6, max_digits=13, )

    salary = models.DecimalField(verbose_name="Salary", null=True, blank=False, default=None, decimal_places=6, max_digits=13, )

