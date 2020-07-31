"""
Copyright © 2020 FC Tools. All rights reserved.
Author: German Yakimov
"""

from django.db import models


class TrafficSource(models.Model):
    """
    This model represents traffic source from corresponding table from tracker
    (http://fcttrk.com/?page=Traffic_Sources).
    """

    id = models.IntegerField(primary_key=True, verbose_name="ID", null=False, blank=False, unique=True, )

    user = models.ForeignKey("User", verbose_name="User", blank=False, null=True, on_delete=models.CASCADE, )

    name = models.CharField(max_length=128, verbose_name="Name", null=True, blank=True, )

    tokens = models.BooleanField(verbose_name="Tokens", null=True, blank=True, )

    campaigns = models.IntegerField(verbose_name="Campaigns", null=True, blank=True, )

    def __str__(self):
        return f"{self.id} {self.name} {self.user.login}" if self.user else f"{self.id} {self.name}"

    def __eq__(self, other):
        if not other:
            return False

        return all([self.id == other.id, self.name == other.name])

    def __hash__(self):
        return hash((self.id, self.name))
