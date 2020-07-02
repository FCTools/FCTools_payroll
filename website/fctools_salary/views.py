# Create your views here.
import os

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, redirect

from fctools_salary.services.binom.update import update_basic_info
from fctools_salary.services.engine.engine import count_user_salary
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

            total_revenue, final_percent, start_balances, profits, from_rev_period, tests, result = \
                count_user_salary(user, start_date, end_date, update_db_flag)

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
                'end_date': end_date})
        else:
            return render(request, os.path.join('fctools_web', 'count.html'), {'form': form})

    else:
        form = ReportInfoForm()
        return render(request, os.path.join('fctools_web', 'count.html'), {'form': form})


def update_db(request):
    update_basic_info()

    return redirect('/admin/fctools_salary/')


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request.POST)

        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            user = authenticate(username=username, password=password)
            login(request, user)

            return redirect('base_menu')
        else:
            return render(request, os.path.join('fctools_web', 'login.html'), {'form': form})

    else:
        form = AuthenticationForm()
        return render(request, os.path.join('fctools_web', 'login.html'), {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')
