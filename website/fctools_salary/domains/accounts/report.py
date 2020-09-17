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

    profit_admin = models.DecimalField(verbose_name="ADMIN profit", null=False, blank=False, decimal_places=6, max_digits=13, )

    profit_native = models.DecimalField(verbose_name="NATIVE profit", null=False, decimal_places=6, max_digits=13, )

    profit_push = models.DecimalField(verbose_name="PUSH profit", null=False, blank=False, decimal_places=6, max_digits=13, )

    profit_pop = models.DecimalField(verbose_name="POP profit", null=False, blank=False, decimal_places=6, max_digits=13, )

    profit_fpa_hsa_pwa = models.DecimalField(verbose_name="FPA/HSA/PWA profit", null=False, decimal_places=6, max_digits=13, )

    profit_inapp = models.DecimalField(verbose_name="INAPP profit", null=False, decimal_places=6, max_digits=13, )

