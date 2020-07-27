from django.db import models
from django.utils.html import format_html


class Test(models.Model):
    """
    This model represents Test.
    This object is formed from test budget, user, some traffic sources and some offers.

    The meaning of this object: this is the amount that an employee can spend free of charge
    on implementing these offers with these traffic sources.
    If the profit is negative, but is covered by the test budget,
    this negative profit is not deducted from the employee's salary.

    Note: each user has balance for each test. E.g. if test amount is 50$ and user profit is -20$,
    his balance for this test will be 30$.
    If user reaches a non-positive balance for some test (test amount spent), that test will be removed.
    """

    budget = models.DecimalField(verbose_name="Budget", null=False, blank=False, decimal_places=6, max_digits=13,)

    user = models.ForeignKey("User", on_delete=models.CASCADE, verbose_name="user", null=False, blank=False,)

    traffic_sources = models.ManyToManyField(
        "TrafficSource", verbose_name="Traffic sources", related_name="tests_list",
    )

    one_budget_for_all_traffic_sources = models.BooleanField(
        verbose_name="One budget for all traffic sources", default=False,
    )

    offers = models.ManyToManyField("Offer", verbose_name="Offers", related_name="tests_list")

    traffic_group = models.CharField(
        max_length=64,
        verbose_name="Traffic group",
        null=False,
        blank=False,
        choices=(
            ("ADMIN", "ADMIN"),
            ("FPA/HSA/PWA", "FPA/HSA/PWA"),
            ("INAPP traff", "INAPP traff"),
            ("NATIVE traff", "NATIVE traff"),
            ("POP traff", "POP traff"),
            ("PUSH traff", "PUSH traff"),
        ),
    )

    balance = models.DecimalField(verbose_name="Balance", blank=False, null=False, decimal_places=6, max_digits=13,)

    geo = models.ManyToManyField("Geo", verbose_name="GEO", blank=True,)

    def budget_rounded(self):
        return round(self.budget, 4)

    budget_rounded.short_description = "Budget"

    def balance_colored(self):
        return format_html(
            f'<span style="color: {"#008000" if self.balance >= 0 else "#FF0000"};">' f"{round(self.balance, 4)}</span>"
        )

    balance_colored.short_description = "Balance"

    def offers_str(self):
        return " ||| ".join(sorted([str(offer) for offer in self.offers.all()]))

    offers_str.short_description = "Offers"

    def traffic_sources_str(self):
        return " ||| ".join(sorted([str(ts) for ts in self.traffic_sources.all()]))

    traffic_sources_str.short_description = "Traffic sources"
