"""
Copyright © 2020-2021 FC Tools.
All rights reserved.
Author: German Yakimov
"""

from django.contrib.admin import SimpleListFilter
from fctools_salary.domains.accounts.user import User


class ActiveUsersFilter(SimpleListFilter):
    title = 'User'
    parameter_name = 'u'

    def lookups(self, request, model_admin):
        return [(user.id, user.login) for user in User.objects.filter(salary_group__gt=0)]

    def queryset(self, request, queryset):
        # print(self.value())
        if self.value():
            return queryset.filter(user_id=self.value())
        return queryset
