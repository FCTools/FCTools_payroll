from django.db import models
from django.utils.html import format_html


class User(models.Model):
    """
    This model is NOT custom django user model.
    This model represents employee from users-table in tracker (http://fcttrk.com/?page=Users) with
    some additional parameters.
    """

    id = models.IntegerField(primary_key=True, verbose_name="ID", null=False, blank=False, unique=True, )

    login = models.CharField(max_length=128, verbose_name="Login", blank=True, null=True, )

    is_lead = models.BooleanField(verbose_name="Teamlead", null=False, blank=False, default=False, )

    """
    This field represents user salary group. Now there are 2 groups: 1 and 2. 
    Each group has conditions and affects the calculations. 
    Default value is -1, this value means that user isn't active and doesn't take part in calculations. 
    """
    salary_group = models.IntegerField(
        verbose_name="Salary group", null=True, blank=False, choices=((-1, -1), (1, 1), (2, 2),), default=-1,
    )

    """
    There are 6 types of traffic (traffic groups) in tracker: ADMIN, FPA/HSA/PWA, INAPP, NATIVE, POP and PUSH. 
    Salary is calculated separately for each type of traffic.
    If salary for some traffic type is negative, 
    we must remember this in database for this user (this value is called balance, if salary for traffic type 
    is non-negative, balance is 0).
    Next 6 fields contains balance for every traffic type.
    """

    admin_balance = models.DecimalField(
        verbose_name="ADMIN balance", null=True, blank=False, default=0, decimal_places=6, max_digits=12,
    )

    fpa_hsa_pwa_balance = models.DecimalField(
        verbose_name="FPA/HSA/PWA balance", null=True, blank=False, default=0, decimal_places=6, max_digits=12,
    )

    inapp_balance = models.DecimalField(
        verbose_name="INAPP balance", null=True, blank=False, default=0, decimal_places=6, max_digits=12,
    )

    native_balance = models.DecimalField(
        verbose_name="NATIVE balance", null=True, blank=False, default=0, decimal_places=6, max_digits=12,
    )

    pop_balance = models.DecimalField(
        verbose_name="POP balance", null=True, blank=False, default=0, decimal_places=6, max_digits=12,
    )

    push_balance = models.DecimalField(
        verbose_name="PUSH balance", null=True, blank=False, default=0, decimal_places=6, max_digits=12,
    )

    def __str__(self):
        return f"{self.id} {self.login}"

    def __eq__(self, other):
        if not other:
            return False

        return all([self.id == other.id, self.login == other.login])

    def __hash__(self):
        return hash((self.id, self.login))


class TrafficSource(models.Model):
    """
    This model represents traffic source from corresponding table from tracker
    (http://fcttrk.com/?page=Traffic_Sources).
    """

    id = models.IntegerField(primary_key=True, verbose_name="ID", null=False, blank=False, unique=True, )

    user = models.ForeignKey(to=User, verbose_name="User", blank=False, null=True, on_delete=models.CASCADE, )

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

    budget = models.DecimalField(verbose_name="Budget", null=False, blank=False, decimal_places=6, max_digits=13, )

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="user", null=False, blank=False, )

    traffic_sources = models.ManyToManyField(TrafficSource, verbose_name="Traffic sources", related_name="tests_list", )

    one_budget_for_all_traffic_sources = models.BooleanField(
        verbose_name="One budget for all traffic sources", default=False,
    )

    offers = models.ManyToManyField(Offer, verbose_name="Offers", related_name="tests_list")

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

    balance = models.DecimalField(verbose_name="Balance", blank=False, null=False, decimal_places=6, max_digits=13, )

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


class Campaign(models.Model):
    """
    This model represents Campaign from tracker (http://fcttrk.com/?page=Campaigns).
    In addition, there is offers_list - many to many field with Offer model.
    """

    id = models.IntegerField(primary_key=True, verbose_name="ID", unique=True, blank=False, null=False, )

    name = models.CharField(max_length=256, verbose_name="Name", null=True, blank=True, )

    traffic_group = models.CharField(
        max_length=16,
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

    traffic_source = models.ForeignKey(
        TrafficSource, on_delete=models.CASCADE, verbose_name="Traffic source", blank=False, null=False,
    )

    revenue = models.DecimalField(verbose_name="Revenue", null=False, blank=False, decimal_places=6, max_digits=12, )

    cost = models.DecimalField(verbose_name="Cost", null=False, blank=False, decimal_places=6, max_digits=12, )

    profit = models.DecimalField(verbose_name="Profit", null=False, blank=False, decimal_places=6, max_digits=12, )

    user = models.ForeignKey(User, verbose_name="User", on_delete=models.CASCADE, null=True, blank=False, )

    offers_list = models.ManyToManyField(Offer, related_name="campaigns_list", verbose_name="Offers", )

    def profit_colored(self):
        if self.profit < 0:
            color_code = "#FF0000"
        elif self.profit > 0:
            color_code = "#008000"
        else:
            color_code = "#D3D3D3"

        return format_html(f'<span style="color: {color_code};">{round(self.profit, 4)}</span>')

    profit_colored.short_description = "Profit"

    def cost_rounded(self):
        return round(self.cost, 4)

    cost_rounded.short_description = "Cost"

    def revenue_rounded(self):
        return round(self.revenue, 4)

    revenue_rounded.short_description = "Revenue"

    def __str__(self):
        return f"{self.id} {self.name}"

    def __eq__(self, other):
        if not other:
            return False

        return all(
            [
                self.id == other.id,
                self.name == other.name,
                self.traffic_group == other.traffic_group,
                self.traffic_source == other.traffic_source,
            ]
        )

    def __hash__(self):
        return hash((self.id, self.name, self.traffic_source))


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
