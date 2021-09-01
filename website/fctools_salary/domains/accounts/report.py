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

    revenue_admin = models.DecimalField(verbose_name="ADMIN revenue", null=True, blank=False, decimal_places=6,
                                        max_digits=13, default=-1, )

    revenue_native = models.DecimalField(verbose_name="NATIVE revenue", null=True, decimal_places=6, max_digits=13,
                                         default=-1, )

    revenue_push = models.DecimalField(verbose_name="PUSH revenue", null=True, blank=False, decimal_places=6,
                                       max_digits=13, default=-1, )

    revenue_pop = models.DecimalField(verbose_name="POP revenue", null=True, blank=False, decimal_places=6,
                                      max_digits=13, default=-1, )

    revenue_fpa_hsa_pwa = models.DecimalField(verbose_name="FPA/HSA/PWA revenue", null=True, decimal_places=6,
                                              max_digits=13, default=-1, )

    revenue_inapp = models.DecimalField(verbose_name="INAPP revenue", null=True, decimal_places=6, max_digits=13,
                                        default=-1, )

    revenue_tik_tok = models.DecimalField(verbose_name="Tik Tok revenue", null=True, decimal_places=6, max_digits=13,
                                          default=-1, )
