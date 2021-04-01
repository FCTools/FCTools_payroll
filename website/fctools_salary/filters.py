# Copyright © 2020-2021 Filthy Claws Tools - All Rights Reserved
#
# This file is part of FCTools_payroll
#
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Author: German Yakimov <german13yakimov@gmail.com>

from django.contrib.admin import SimpleListFilter
from fctools_salary.domains.accounts.user import User


class ActiveUsersFilter(SimpleListFilter):
    title = 'User'
    parameter_name = 'u'

    def lookups(self, request, model_admin):
        return [(user.id, user.login) for user in User.objects.filter(salary_group__gt=0)]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(user_id=self.value())
        return queryset
