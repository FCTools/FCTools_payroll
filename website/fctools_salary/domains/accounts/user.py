"""
Copyright © 2020 FC Tools. All rights reserved.
Author: German Yakimov
"""

from django.db import models


class User(models.Model):
    """
    This model is NOT custom django user.
    This model represents employee from users table in tracker (http://fcttrk.com/?page=Users) with
    some additional parameters (salary group and balances for each traffic group).
    """

    id = models.IntegerField(primary_key=True, verbose_name="ID", null=False, blank=False, unique=True, )

    login = models.CharField(max_length=128, verbose_name="Login", blank=True, null=True, )

    is_lead = models.BooleanField(verbose_name="Teamlead", null=False, blank=False, default=False, )

    """
    This field represents user's salary group. Now there are 3 groups: 1, 2 and 3. 
    Each group has conditions (hardcoded in engine) and affects the calculations. 
    Default value is -1, this value means that user isn't active and doesn't take part in calculations. 
    """
    salary_group = models.IntegerField(
        verbose_name="Salary group", null=True, blank=False, choices=((-1, -1), (1, 1), (2, 2), (3, 3), ), default=-1,
    )

    """
    There are 6 types of traffic (traffic groups) in tracker: ADMIN, FPA/HSA/PWA, INAPP, NATIVE, POP and PUSH. 
    Salary is calculated separately for each traffic group.
    If salary for some traffic group is negative, 
    system must remember this in database for this user (this value is called balance, if salary for traffic type 
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

    tik_tok_balance = models.DecimalField(
        verbose_name="Tik Tok balance", null=True, blank=False, default=0, decimal_places=6, max_digits=12,
    )

    def __str__(self):
        return f"{self.id} {self.login}"

    def __eq__(self, other):
        if not other:
            return False

        return all([self.id == other.id, self.login == other.login])

    def __hash__(self):
        return hash((self.id, self.login))
