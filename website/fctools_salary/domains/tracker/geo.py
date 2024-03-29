# Copyright © 2020-2021 Filthy Claws Tools - All Rights Reserved
#
# This file is part of FCTools_payroll
#
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Author: German Yakimov <german13yakimov@gmail.com>

from django.db import models


class Geo(models.Model):
    """
    This model represents geo (country). Basically it's two strings - country name and iso 2-letters code.
    """

    country = models.CharField(max_length=128, verbose_name="Country", null=False, blank=False, )
    iso_code = models.CharField(max_length=2, verbose_name="ISO Code", null=False, blank=False, )

    class Meta:
        verbose_name = "GEO"
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.country}; {self.iso_code}"
