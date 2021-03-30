"""
Copyright © 2020-2021 FC Tools.
All rights reserved.
Author: German Yakimov
"""

import functools
import logging
import os
import traceback

from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LogoutView as DJLogoutView
from django.db import transaction
from django.shortcuts import render

from fctools_salary.services.binom.update import update_basic_info
from fctools_salary.services.engine.engine import calculate_user_salary
from .forms import CalculationForm

_logger = logging.getLogger(__name__)


def _return(request, error_message, traceback_, status_code=200):
    """
    :param request: request
    :param error_message: error message
    :param traceback_: formatted traceback
    :param status_code: response status code
    :return: Readable http-response with error message and traceback (support cyrillic symbols)
    """

    template = "error.html"

    return render(request, template,
                  context={"title": "Internal Server Error", "error_message": error_message,
                           "traceback": traceback_,
                           "status_code": status_code})


def error_response(request, exception):
    """
    Form error message and traceback.
    :param exception: exception
    :param request: request
    :return: return-method, that returns rendered http-response with error, traceback and status_code
    """

    return _return(request, str(exception), traceback.format_exc(), status_code=500)


def base_view(view):
    """
    Base view with all exceptions handling.
    :param view: view to decorate
    :return: decorated view
    """

    @functools.wraps(view)
    def inner(request, *args, **kwargs):
        try:
            with transaction.atomic():
                return view(request, *args, **kwargs)
        except Exception as exception:
            _logger.error(str(exception))
            return error_response(request, exception)

    return inner


@base_view
@login_required(login_url="/login/")
def base_menu(request):
    """
    Base menu, contains two buttons: edit db and count salary.
    Login required.
    :param request: request
    :return: main menu page
    """

    template = os.path.join("fctools_salary", "menu.html")
    user = request.user.username

    return render(request, template, context={"user": user})


@base_view
@login_required(login_url="/login/")
def count_view(request):
    """
    View with form for calculation configuration.
    :param request: request
    :return: if form is valid, calculate salary and returns result page (count_result.html)
    """

    form_template = os.path.join("fctools_salary", "count.html")
    result_template = os.path.join("fctools_salary", "count_result.html")

    if request.method == "POST":
        form = CalculationForm(request.POST)

        if form.is_valid():
            user = form.cleaned_data["user"]
            start_date = form.cleaned_data["start_date"]
            end_date = form.cleaned_data["end_date"]
            update_db_flag = form.cleaned_data["update_db"]
            traffic_groups = form.cleaned_data["traffic_groups"]
            cost = form.cleaned_data["cost"]

            if cost and len(traffic_groups) > 1:
                _logger.warning("Incorrect report form: manual cost and more than 1 traffic source.")
                return render(request, form_template, {"form": form})

            update_basic_info()

            return render(
                request,
                result_template,
                context=calculate_user_salary(user, start_date, end_date, update_db_flag, traffic_groups, cost=cost),
            )
        else:
            _logger.warning("Incorrect report form.")
            return render(request, form_template, {"form": form})

    else:
        form = CalculationForm()
        return render(request, form_template, {"form": form})


class LogoutView(DJLogoutView):
    next_page = "login"
