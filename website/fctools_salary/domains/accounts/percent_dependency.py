from django.db import models

from fctools_salary.domains.accounts.user import User


class PercentDependency(models.Model):
    """
    Each teamlead has employees in his own structure. This teamlead gets some percent from salary of these employees
    every time we calculate salary (in the end of the period). This model represents this relations.
    """

    from_user = models.ForeignKey(
        User, related_name="user_from", on_delete=models.CASCADE, verbose_name="From", null=False, blank=False,
    )

    to_user = models.ForeignKey(
        User, related_name="user_to", on_delete=models.CASCADE, verbose_name="To", null=False, blank=False,
    )

    percent = models.FloatField(verbose_name="Percent", null=False, blank=False, )

    class Meta:
        verbose_name = "Percent dependency"
        verbose_name_plural = "Percent dependencies"

    def __str__(self):
        return f"id: {self.id}, from_user: {self.from_user}, to_user: {self.to_user}"
