from django.db import models


class Geo(models.Model):
    """
    This model represents geo. Basically it's two strings - country name and shortcut.
    """

    country = models.CharField(max_length=128, verbose_name="Country", null=False, blank=False,)
    iso_code = models.CharField(max_length=2, verbose_name="ISO Code", null=False, blank=False,)

    class Meta:
        verbose_name = "GEO"
        verbose_name_plural = verbose_name
