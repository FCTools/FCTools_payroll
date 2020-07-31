"""
Copyright © 2020 FC Tools. All rights reserved.
Author: German Yakimov
"""

from django.db import models


class Offer(models.Model):
    """
    This model represents offer from corresponding table from tracker (http://fcttrk.com/?page=Offers).
    """

    id = models.IntegerField(primary_key=True, verbose_name="ID", null=False, blank=False, unique=True, )

    geo = models.CharField(max_length=32, verbose_name="GEO", null=True, blank=True, )

    name = models.CharField(max_length=256, verbose_name="Name", null=False, blank=False, )

    group = models.CharField(max_length=64, verbose_name="Group", null=True, blank=True, )

    network = models.CharField(max_length=64, verbose_name="Network", null=True, blank=True, )

    def __str__(self):
        return self.name

    def __eq__(self, other):
        if not other:
            return False

        return all(
            [
                self.id == other.id,
                self.name == other.name,
                self.geo == other.geo,
                self.group == other.group,
                self.network == other.network,
            ]
        )

    def __hash__(self):
        return hash((self.id, self.name, self.geo, self.group, self.network))
