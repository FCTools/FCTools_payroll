"""
Copyright © 2020-2021 FC Tools.
All rights reserved.
Author: German Yakimov
"""

import logging
from datetime import date
from typing import List, Dict

from django.conf import settings
from django.db import transaction

from fctools_salary.domains.accounts.percent_dependency import PercentDependency
from fctools_salary.domains.accounts.test import Test
from fctools_salary.domains.tracker.campaign import Campaign
from fctools_salary.domains.tracker.offer import Offer
from fctools_salary.services.binom.get_info import get_campaigns
from fctools_salary.services.binom.update import update_offers
from fctools_salary.services.engine.tests_manager import TestsManager
from fctools_salary.services.engine.tracker_manager import TrackerManager
from fctools_salary.services.helpers.redis_client import RedisClient
from fctools_salary.services.helpers.report import Report as Rp

_logger = logging.getLogger(__name__)


def _calculate_final_percent(revenue, salary_group):
    """
    Calculate final percent based on total revenue for the period and user salary group.
    :param revenue: total revenue for the period
    :type revenue: float
    :param salary_group: user salary group
    :type salary_group: int
    :return final percent based on user salary group and total revenue
    :rtype: float
    """

    percent = 0

    if salary_group == 1:
        percent = 0.5

        if revenue > 10000:
            percent = 0.6
        elif revenue > 5000:
            percent = 0.55
    elif salary_group == 2:
        percent = 0.3

        if revenue > 20000:
            percent = 0.4
        elif revenue > 10000:
            percent = 0.35

    return percent


def _set_start_balances(user, traffic_groups):
    """
    Get user balances for selected traffic groups from database.
    :param user: user to get start balances
    :type user: User
    :param traffic_groups: traffic groups which balances needed
    :type traffic_groups: List[str]
    :return: start balance (from database) for each traffic group in traffic_groups
    :rtype: Dict[str, float]
    """

    result = {}

    if settings.ADMIN in traffic_groups:
        settings.ADMIN = round(float(user.admin_balance), 6)
    if settings.FPA_HSA_PWA in traffic_groups:
        result[settings.FPA_HSA_PWA] = round(float(user.fpa_hsa_pwa_balance), 6)
    if settings.INAPP_TRAFF in traffic_groups:
        result[settings.INAPP_TRAFF] = round(float(user.inapp_balance), 6)
    if settings.NATIVE_TRAFF in traffic_groups:
        result[settings.NATIVE_TRAFF] = round(float(user.native_balance), 6)
    if settings.POP_TRAFF in traffic_groups:
        result[settings.POP_TRAFF] = round(float(user.pop_balance), 6)
    if settings.PUSH_TRAFF in traffic_groups:
        result[settings.PUSH_TRAFF] = round(float(user.push_balance), 6)
    if settings.TIK_TOK in traffic_groups:
        result[settings.TIK_TOK] = round(float(user.tik_tok_balance), 6)

    return result


def _calculate_teamlead_profit_from_other_users(start_date, end_date, user, traffic_groups):
    """
    Calculate teamlead profit from other users.
    :param start_date: period start date
    :type start_date: date
    :param end_date: period end date
    :type end_date: date
    :param user: user (teamlead)
    :type user: User
    :param traffic_groups: traffic groups that includes in calculation
    :type traffic_groups: List[str]
    :return: profit from other users with detailed calculation (split by traffic groups)
    :rtype: Dict[str, List[Union[str, float]]]
    """

    from_other_users = {traffic_group: ["", 0.0] for traffic_group in traffic_groups}

    dependencies_list = PercentDependency.objects.all().filter(to_user=user)

    for dependency in dependencies_list:
        TestsManager.archive_user_tests(dependency.from_user)
        profit_with_tests = TestsManager.calculate_profit_with_tests(dependency.from_user, start_date, end_date,
                                                                     traffic_groups)

        for traffic_group in profit_with_tests:
            profit_from_user = round(profit_with_tests[traffic_group] * dependency.percent, 6)

            if profit_from_user > 0:
                from_other_users[traffic_group][1] += profit_from_user

                if not from_other_users[traffic_group][0]:
                    from_other_users[traffic_group][0] = f"{profit_from_user}" f" [{dependency.from_user.login}]"
                else:
                    from_other_users[traffic_group][0] += f" + {profit_from_user}" f" [{dependency.from_user.login}]"

    for traffic_group in from_other_users:
        if from_other_users[traffic_group][1] > 0:
            if "+" in from_other_users[traffic_group][0]:
                from_other_users[traffic_group][0] += f" = {from_other_users[traffic_group][1]}"
        else:
            from_other_users[traffic_group][0] = "0.0"

    return from_other_users


def _save_campaigns(campaigns_to_save, campaigns_db):
    """
    Save campaigns to database (or update statistics, if campaign already exists).
    :param campaigns_to_save: campaigns to save
    :type campaigns_to_save: List[CampaignTracker]
    :param campaigns_db: current campaigns from database
    :type campaigns_db: List[Campaign]
    :return: None
    """

    with transaction.atomic():
        for campaign in campaigns_to_save:
            if campaign["instance"] not in campaigns_db:
                campaign["instance"].save()

                for offer_id in campaign["offers_list"]:
                    try:
                        offer = Offer.objects.get(id=offer_id)
                    except Offer.DoesNotExist:
                        update_offers()

                        try:
                            offer = Offer.objects.get(id=offer_id)
                        except Offer.DoesNotExist:
                            _logger.error(f"Campaign {campaign['instance'].id} has unknown offer: {offer_id}")
                            continue

                    campaign["instance"].offers_list.add(offer)

            campaign["instance"].save()


def calculate_user_salary(user, start_date, end_date, commit, traffic_groups, cost=None):
    report = Rp()
    report.user = user
    report.start_date = start_date
    report.end_date = end_date

    redis_client = RedisClient()

    _logger.info(f"Start salary calculating from {start_date} to {end_date} for user {user}")

    report.traffic_groups = traffic_groups
    report.start_balances = _set_start_balances(user, traffic_groups)

    _logger.info("Start balances was successfully set.")

    prev_campaigns_db_list = list(Campaign.objects.filter(user=user))
    current_campaigns_tracker_list = get_campaigns(start_date, end_date, user, redis_client)

    _logger.info("Successfully get campaigns info (database and tracker, current and previous period).")

    report.revenues, report.profits = TrackerManager.calculate_profit_for_period(current_campaigns_tracker_list,
                                                                                 traffic_groups, cost=cost)

    _logger.info(f"Total revenue and profits was successfully calculated. "
                 f"Revenues: {report.revenues}. Profits: {report.profits}")

    report.deltas = TrackerManager.calculate_deltas(user, traffic_groups, commit, redis_client)

    TestsManager.archive_user_tests(user)
    tests_list = list(Test.objects.filter(user=user, archived=False).prefetch_related('offers', 'traffic_sources',
                                                                                      'geo'))

    redis_client.clear()

    report.tests = TestsManager.calculate_tests(tests_list, current_campaigns_tracker_list, commit, traffic_groups,
                                                start_date, end_date)
    _logger.info(f"Tests was successfully calculated: {report.tests}")

    report.final_percents = {traffic_group: _calculate_final_percent(report.revenues[traffic_group], user.salary_group)
                             for traffic_group in traffic_groups}

    _logger.info(f"Final percents: {report.final_percents}. User is lead: {user.is_lead}")

    if user.is_lead:
        report.from_other_users = _calculate_teamlead_profit_from_other_users(start_date, end_date, user,
                                                                              traffic_groups)
        _logger.info(f"User profit from other users (as teamlead): {report.from_other_users}")

    report.generate_calculation()
    report_filename = report.generate_pdf()

    if commit:
        report.save()
        _save_campaigns(current_campaigns_tracker_list, prev_campaigns_db_list)

    return {
        "user": str(user),
        "start_date": start_date,
        "end_date": end_date,
        "start_balances": report.start_balances,
        "revenues": report.revenues,
        "final_percents": report.final_percents,
        "profits": report.profits,
        "from_prev_period": report.deltas,
        "tests": report.tests,
        "result": report.result,
        "report_name": report_filename,
        "from_other_users": report.from_other_users if report.from_other_users else None
    }