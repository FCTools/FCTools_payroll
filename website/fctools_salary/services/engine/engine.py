"""
Copyright © 2020 FC Tools. All rights reserved.
Author: German Yakimov
"""

import logging
from copy import deepcopy
from datetime import timedelta, date
from typing import List, Dict

from django.db import transaction

from fctools_salary.domains.accounts.percent_dependency import PercentDependency
from fctools_salary.domains.accounts.test import Test
from fctools_salary.domains.tracker.campaign import Campaign
from fctools_salary.domains.tracker.offer import Offer
from fctools_salary.services.binom.get_info import get_campaigns
from fctools_salary.services.binom.update import update_offers
from fctools_salary.services.engine.tests_manager import TestsManager
from fctools_salary.services.engine.tracker_manager import TrackerManager
from fctools_salary.services.helpers.pdf_generator import PDFGenerator

_logger = logging.getLogger(__name__)


def _calculate_final_percent(revenue, salary_group):
    """
    Calculates final percent based on total revenue for the period and user salary group.

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
    elif salary_group == 3:
        percent = 0.15

    return percent


def _set_start_balances(user, traffic_groups):
    """
    Gets user balances for selected traffic groups from database.

    :param user: user to get start balances
    :type user: User

    :param traffic_groups: traffic groups which balances needed
    :type traffic_groups: List[str]

    :return: start balance (from database) for each traffic group in traffic_groups
    :rtype: Dict[str, float]
    """

    result = {}

    if "ADMIN" in traffic_groups:
        result["ADMIN"] = round(float(user.admin_balance), 6)
    if "FPA/HSA/PWA" in traffic_groups:
        result["FPA/HSA/PWA"] = round(float(user.fpa_hsa_pwa_balance), 6)
    if "INAPP traff" in traffic_groups:
        result["INAPP traff"] = round(float(user.inapp_balance), 6)
    if "NATIVE traff" in traffic_groups:
        result["NATIVE traff"] = round(float(user.native_balance), 6)
    if "POP traff" in traffic_groups:
        result["POP traff"] = round(float(user.pop_balance), 6)
    if "PUSH traff" in traffic_groups:
        result["PUSH traff"] = round(float(user.push_balance), 6)

    return result


def _calculate_teamlead_profit_from_other_users(start_date, end_date, user, traffic_groups):
    """
    Calculates teamlead profit from other users.

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


def _save_user_balances(user, balances):
    """
    Saves user balances to database.

    :param user: user
    :type user: User

    :param balances: balances to save (split by traffic group)
    :type balances: Dict[str, float]

    :return: None
    """

    with transaction.atomic():
        user.admin_balance = balances["ADMIN"] if "ADMIN" in balances and balances["ADMIN"] < 0 else 0
        user.fpa_hsa_pwa_balance = (
            balances["FPA/HSA/PWA"] if "FPA/HSA/PWA" in balances and balances["FPA/HSA/PWA"] < 0 else 0
        )
        user.inapp_balance = balances["INAPP traff"] if "INAPP traff" in balances and balances["INAPP traff"] < 0 else 0
        user.native_balance = (
            balances["NATIVE traff"] if "NATIVE traff" in balances and balances["NATIVE traff"] < 0 else 0
        )
        user.pop_balance = balances["POP traff"] if "POP traff" in balances and balances["POP traff"] < 0 else 0
        user.push_balance = balances["PUSH traff"] if "PUSH traff" in balances and balances["PUSH traff"] < 0 else 0

        user.save()


def _save_campaigns(campaigns_to_save, campaigns_db):
    """
    Saves campaigns to database (or update statistics, if campaign already exists).

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
                        offer = Offer.objects.get(id=offer_id)

                    campaign["instance"].offers_list.add(offer)

            campaign["instance"].save()


def calculate_user_salary(user, start_date, end_date, commit, traffic_groups) -> dict:
    """
    Calculates user salary for the period from start_date to end_date by selected traffic groups. Generates
    pdf-file with result-table.

    :param user: user
    :type user: User

    :param start_date: period start date
    :type start_date: date

    :param end_date: period end date
    :type end_date: date

    :param commit: if set to True, than all changes will be committed to database (e.g. tests balances,
    campaigns statistics and user balances)
    :type commit: bool

    :param traffic_groups: traffic groups that includes in calculation
    :type traffic_groups: List[str]

    :return: Detailed calculation
    :rtype: Dict[str, Union[
    float,
    Dict[str, float],
    Dict[str, List[Union[str, float]]],
    Optional[Dict[str, List[Union[str, float]]]],
    str]
    """

    _logger.info(f"Start salary calculating from {start_date} to {end_date} for user {user}")

    result = _set_start_balances(user, traffic_groups)
    start_balances = deepcopy(result)

    _logger.info("Start balances was successfully set.")

    prev_campaigns_db_list = list(Campaign.objects.filter(user=user))
    prev_campaigns_tracker_list = get_campaigns(start_date - timedelta(days=14), start_date - timedelta(days=1), user)
    current_campaigns_tracker_list = get_campaigns(start_date, end_date, user)

    _logger.info("Successfully get campaigns info (database and tracker, current and previous period).")

    total_revenue, profits = TrackerManager.calculate_profit_for_period(current_campaigns_tracker_list, traffic_groups)

    _logger.info("Total revenue and profits was successfully calculated.")
    _logger.info(f"Total revenue: {total_revenue}")
    _logger.info(f"Profits: {profits}")

    deltas = TrackerManager.calculate_deltas(prev_campaigns_tracker_list, prev_campaigns_db_list, traffic_groups)

    _logger.info(f"Deltas was successfully calculated: {deltas}")

    TestsManager.archive_user_tests(user)
    tests_list = list(Test.objects.filter(user=user, archived=False))
    tests = TestsManager.calculate_tests(tests_list, current_campaigns_tracker_list, commit, traffic_groups, start_date,
                                         end_date)

    _logger.info(f"Tests was successfully calculated: {tests}")

    final_percent = _calculate_final_percent(total_revenue, user.salary_group)

    _logger.info(f"Final percent: {final_percent}")
    _logger.info(f"User is lead: {user.is_lead}")

    from_other_users = None
    if user.is_lead:
        from_other_users = _calculate_teamlead_profit_from_other_users(start_date, end_date, user, traffic_groups)
        _logger.info(f"User profit from other users (as teamlead): {from_other_users}")

    for traffic_group in result:
        result[traffic_group] += round(profits[traffic_group], 6)
        result[traffic_group] += round(deltas[traffic_group][1], 6)
        result[traffic_group] += round(tests[traffic_group][1], 6)

        if result[traffic_group] > 0:
            result[traffic_group] *= final_percent

        if user.is_lead:
            result[traffic_group] += from_other_users[traffic_group][1]

        result[traffic_group] = ["", result[traffic_group]]

        if result[traffic_group][1] >= 0:
            result[traffic_group][0] = (
                f"({start_balances[traffic_group]}"
                f'{f" + {profits[traffic_group]}" if profits[traffic_group] >= 0 else f" - {-profits[traffic_group]}"}'
                f" + {deltas[traffic_group][1]} + "
                f"{tests[traffic_group][1]}) * {final_percent}"
            )
        else:
            result[traffic_group][0] = (
                f"{start_balances[traffic_group]}"
                f'{f" + {profits[traffic_group]}" if profits[traffic_group] >= 0 else f" - {-profits[traffic_group]}"}'
                f" + {deltas[traffic_group][1]} + "
                f"{tests[traffic_group][1]}"
            )

        if user.is_lead and from_other_users[traffic_group][1] > 0:
            result[traffic_group][0] += f" + {from_other_users[traffic_group][1]}"

        result[traffic_group][1] = round(result[traffic_group][1], 6)
        result[traffic_group][0] += f" = {result[traffic_group][1]}"

    _logger.info(f"Commit: {commit}")

    if commit:
        _save_user_balances(user, {traffic_group: result[traffic_group][1] for traffic_group in result})
        _logger.info("User balances was successfully saved.")

        _save_campaigns(current_campaigns_tracker_list, prev_campaigns_db_list)
        _logger.info("Campaigns was successfully saved.")

    _logger.info(f"Final calculation: {result}")

    calculation_items = {
        "start_balances": start_balances,
        "profits": profits,
        "from_prev_period": deltas,
        "tests": tests,
        "result": result,
        "total_revenue": round(total_revenue, 6),
        "final_percent": final_percent,
        "user": user,
        "start_date": start_date,
        "end_date": end_date,
        "from_other_users": from_other_users,
    }

    calculation_items['report_name'] = PDFGenerator.generate_report(**calculation_items)

    return calculation_items
