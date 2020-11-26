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

    profit_admin = models.DecimalField(verbose_name="ADMIN profit", null=True, decimal_places=6,
                                       max_digits=13, default=None, )

    profit_native = models.DecimalField(verbose_name="NATIVE profit", null=True, decimal_places=6, max_digits=13,
                                        default=None, )

    profit_push = models.DecimalField(verbose_name="PUSH profit", null=True, decimal_places=6,
                                      max_digits=13, default=None, )

    profit_pop = models.DecimalField(verbose_name="POP profit", null=True, decimal_places=6,
                                     max_digits=13, default=None, )

    profit_fpa_hsa_pwa = models.DecimalField(verbose_name="FPA/HSA/PWA profit", null=True, decimal_places=6,
                                             max_digits=13, default=None, )

    profit_inapp = models.DecimalField(verbose_name="INAPP profit", null=True, decimal_places=6, max_digits=13,
                                       default=None, )

    profit_tik_tok = models.DecimalField(verbose_name="Tik Tok profit", null=True, decimal_places=6, max_digits=13,
                                         default=None, )

    percent_admin = models.DecimalField(verbose_name="ADMIN percent", null=True, decimal_places=3, max_digits=3,
                                        default=None, )

    percent_native = models.DecimalField(verbose_name="NATIVE percent", null=True, decimal_places=3, max_digits=3,
                                         default=None, )

    percent_push = models.DecimalField(verbose_name="PUSH percent", null=True, decimal_places=3, max_digits=3,
                                       default=None, )

    percent_pop = models.DecimalField(verbose_name="POP percent", null=True, decimal_places=3, max_digits=3,
                                      default=None, )

    percent_fpa_hsa_pwa = models.DecimalField(verbose_name="FPA/HSA/PWA percent", null=True, decimal_places=3,
                                              max_digits=3,
                                              default=None, )

    percent_inapp = models.DecimalField(verbose_name="INAPP percent", null=True, decimal_places=3, max_digits=3,
                                        default=None, )

    percent_tik_tok = models.DecimalField(verbose_name="Tik Tok percent", null=True, decimal_places=3, max_digits=3,
                                          default=None, )
