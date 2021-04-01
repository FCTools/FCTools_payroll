# Copyright © 2020-2021 Filthy Claws Tools - All Rights Reserved
#
# This file is part of FCTools_payroll
#
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Author: German Yakimov <german13yakimov@gmail.com>

from django.db import models


class PercentDependency(models.Model):
    """
    Each teamlead has employees in his own structure. Teamlead gets some percent from salary
    (exactly not salary, profits and tests) of these employees every time we calculate salary
    (in the end of the period). This model represents relations between users (from user - to user - percent).
    """

    from_user = models.ForeignKey(
        "User", related_name="user_from", on_delete=models.CASCADE, verbose_name="From", null=False, blank=False,
    )

    to_user = models.ForeignKey(
        "User", related_name="user_to", on_delete=models.CASCADE, verbose_name="To", null=False, blank=False,
    )

    percent = models.FloatField(verbose_name="Percent", null=False, blank=False, )

    class Meta:
        verbose_name = "Percent dependency"
        verbose_name_plural = "Percent dependencies"

    def __str__(self):
        return f"{self.from_user} gets {self.percent} from {self.to_user}"
