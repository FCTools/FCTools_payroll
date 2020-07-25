import functools
import os
import traceback

from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LogoutView as DJLogoutView
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import render, redirect

from fctools_salary.services.binom.update import update_basic_info
from fctools_salary.services.engine.engine import calculate_user_salary
from .forms import ReportInfoForm


def _return(json_object, status_code=200):
    """
    :param json_object: json-object with error message and traceback
    :param status_code: response status code
    :return: Readable json response with error message and traceback (support cyrillic symbols)
    """

    return JsonResponse(json_object, status=status_code, safe=not isinstance(json_object, list),
                        json_dumps_params={'ensure_ascii': False, 'indent': 4})


def error_response(exception):
    """
    Form json-object with error message and traceback.

    :param exception: exception
    :return: _return-method, that returns json response with json-object with error and traceback
    """

    result = {"error_message": str(exception), "traceback": traceback.format_exc()}
    return _return(result, status_code=500)


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
            return error_response(exception)

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

    context = {"user": user}

    return render(request, template, context)


@base_view
@login_required(login_url="/login/")
def count_view(request):
    if request.method == "POST":
        form = ReportInfoForm(request.POST)

        if form.is_valid():
            user = form.cleaned_data["user"]
            start_date = form.cleaned_data["start_date"]
            end_date = form.cleaned_data["end_date"]
            update_db_flag = form.cleaned_data["update_db"]
            traffic_groups = form.cleaned_data["traffic_groups"]

            update_basic_info()
            (
                total_revenue,
                final_percent,
                start_balances,
                profits,
                from_rev_period,
                tests,
                from_other,
                result,
            ) = calculate_user_salary(user, start_date, end_date, update_db_flag, traffic_groups)

            return render(
                request,
                os.path.join("fctools_salary", "count_result.html"),
                context={
                    "start_balances": start_balances,
                    "profits": profits,
                    "from_prev_period": from_rev_period,
                    "tests": tests,
                    "result": result,
                    "total_revenue": total_revenue,
                    "final_percent": final_percent,
                    "user": user,
                    "start_date": start_date,
                    "end_date": end_date,
                    "from_other_users": from_other,
                },
            )
        else:
            return render(request, os.path.join("fctools_salary", "count.html"), {"form": form})

    else:
        form = ReportInfoForm()
        return render(request, os.path.join("fctools_salary", "count.html"), {"form": form})


@base_view
@login_required(login_url="/login/")
def update_db(request):
    update_basic_info()

    return redirect("/admin/fctools_salary/")


class LogoutView(DJLogoutView):
    next_page = "login"
