# Copyright © 2020-2021 Filthy Claws Tools - All Rights Reserved
#
# This file is part of FCTools_payroll
#
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Author: German Yakimov <german13yakimov@gmail.com>

import logging

from django.urls import reverse

from fctools_salary.services.binom.update import update_basic_info
from fctools_salary.views import error_response

_logger = logging.getLogger(__name__)


class UpdateDatabaseMiddleware:
    """
    Middleware for database updating.
    If request's path is "/admin/fctools_salary" (user is going to edit salary database)
    or "/count" (user is going to calculate something), this middleware updates database
    (gets current information from tracker).
    """

    def __init__(self, get_response):
        self._get_response = get_response

    def __call__(self, request):
        try:
            if (request.method == 'GET' and request.path == '/admin/fctools_salary/') or \
                    (request.method == 'POST' and request.path == reverse('count')):
                update_basic_info()
        except Exception as exception:
            _logger.error(str(exception))
            return error_response(request, exception)

        return self._get_response(request)
