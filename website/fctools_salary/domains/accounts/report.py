# Copyright © 2020-2021 Filthy Claws Tools - All Rights Reserved
#
# This file is part of FCTools_payroll
#
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Author: German Yakimov <german13yakimov@gmail.com>

from django.db import models


class Report(models.Model):
    """
    This model represents salary report for period.
    """

    user = models.ForeignKey(to="User", verbose_name="User", null=False, blank=False, on_delete=models.DO_NOTHING, )

    start_date = models.DateField(verbose_name="Start date", null=False, blank=False, )

    end_date = models.DateField(verbose_name="End date", null=False, blank=False, )

    revenue_admin = models.DecimalField(verbose_name="ADMIN profit", null=True, blank=False, decimal_places=6,
                                        max_digits=13, default=None, )

    revenue_native = models.DecimalField(verbose_name="NATIVE profit", null=True, decimal_places=6, max_digits=13,
                                         default=None, )

    revenue_push = models.DecimalField(verbose_name="PUSH profit", null=True, blank=False, decimal_places=6,
                                       max_digits=13, default=None, )

    revenue_pop = models.DecimalField(verbose_name="POP profit", null=True, blank=False, decimal_places=6,
                                      max_digits=13, default=None, )

    revenue_fpa_hsa_pwa = models.DecimalField(verbose_name="FPA/HSA/PWA profit", null=True, decimal_places=6,
                                              max_digits=13, default=None, )

    revenue_inapp = models.DecimalField(verbose_name="INAPP profit", null=True, decimal_places=6, max_digits=13,
                                        default=None, )

    revenue_tik_tok = models.DecimalField(verbose_name="Tik Tok profit", null=True, decimal_places=6, max_digits=13,
                                          default=None, )
