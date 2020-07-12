import os

from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LogoutView as DJLogoutView
from django.shortcuts import render, redirect

from fctools_salary.services.binom.update import update_basic_info
from fctools_salary.services.engine.engine import calculate_user_salary
from .forms import ReportInfoForm


@login_required(login_url='login/')
def base_menu(request):
    template = os.path.join('fctools_web', 'menu.html')
    user = request.user.username

    context = {'user': user}

    return render(request, template, context)


@login_required(login_url='login/')
def count_view(request):
    if request.method == 'POST':
        form = ReportInfoForm(request.POST)

        if form.is_valid():
            user = form.cleaned_data['user']
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']
            update_db_flag = form.cleaned_data['update_db']
            traffic_groups = form.cleaned_data['traffic_groups']

            update_basic_info()
            total_revenue, final_percent, start_balances, profits, from_rev_period, tests, from_other, result = \
                calculate_user_salary(user, start_date, end_date, update_db_flag, traffic_groups)

            return render(request, os.path.join('fctools_web', 'count_result.html'), context={
                'start_balances': start_balances,
                'profits': profits,
                'from_prev_period': from_rev_period,
                'tests': tests,
                'result': result,
                'total_revenue': total_revenue,
                'final_percent': final_percent,
                'user': user,
                'start_date': start_date,
                'end_date': end_date,
                'from_other_users': from_other})
        else:
            return render(request, os.path.join('fctools_web', 'count.html'), {'form': form})

    else:
        form = ReportInfoForm()
        return render(request, os.path.join('fctools_web', 'count.html'), {'form': form})


@login_required(login_url='login/')
def update_db(request):
    update_basic_info()

    return redirect('/admin/fctools_salary/')


class LogoutView(DJLogoutView):
    next_page = 'login'
