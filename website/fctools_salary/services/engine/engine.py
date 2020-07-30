import logging
import os
from copy import deepcopy, copy
from datetime import timedelta, date
from typing import List, Dict, Tuple
from uuid import uuid4

from django.db import transaction
from reportlab.lib import colors
from reportlab.lib.colors import darkgray
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

from fctools_salary.domains.accounts.percent_dependency import PercentDependency
from fctools_salary.domains.accounts.test import Test
from fctools_salary.domains.tracker.campaign import Campaign
from fctools_salary.domains.tracker.offer import Offer
from fctools_salary.exceptions import UpdateError, TestNotSplitError
from fctools_salary.services.binom.get_info import get_campaigns, get_campaign_main_geo
from fctools_salary.services.binom.update import update_offers

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

    if salary_group == 1:
        percent = 0.5

        if revenue > 10000:
            percent = 0.6
        elif revenue > 5000:
            percent = 0.55
    else:
        percent = 0.3

        if revenue > 20000:
            percent = 0.4
        elif revenue > 10000:
            percent = 0.35

    return percent


def _calculate_profit_with_tests(user, start_date, end_date, traffic_groups):
    """
    Calculates user profit for the period including tests

    :param user: User
    :type user: User

    :param start_date: date
    :type start_date: date

    :param end_date: date
    :type end_date: date

    :param traffic_groups: User
    :type traffic_groups: List[str]

    :return user profit from start_date to end_date including tests
    :rtype: Dict[str, float]
    """

    result = {traffic_group: 0.0 for traffic_group in traffic_groups}

    current_campaigns_tracker = get_campaigns(start_date, end_date, user)

    if not current_campaigns_tracker:
        raise UpdateError(message=f"Can't get campaigns from {start_date} to {end_date} for user {user}")

    profit = _calculate_profit_for_period(current_campaigns_tracker, traffic_groups)[1]

    tests_list = list(Test.objects.filter(user=user))
    tests = _calculate_tests(tests_list, current_campaigns_tracker, False, traffic_groups, start_date, end_date)

    for traffic_group in result:
        result[traffic_group] += profit[traffic_group] + tests[traffic_group][1]

    return result


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


def _calculate_profit_for_period(campaigns_list, traffic_groups):
    """
    Calculates profit for the period without tests (just sum profit for all user campaigns).

    :param campaigns_list: list of campaigns for period with current traffic statistics
    :type campaigns_list: List[CampaignTracker]

    :param traffic_groups: traffic groups that includes in calculation
    :type traffic_groups: List[str]

    :return: total revenue and profit for this period (split by traffic groups)
    :rtype: Tuple[float, Dict[str, float]]
    """

    profit = {traffic_group: 0.0 for traffic_group in traffic_groups}
    total_revenue = 0.0

    for campaign in campaigns_list:
        total_revenue += float(campaign["instance"].revenue)

        if campaign["instance"].traffic_group in traffic_groups:
            profit[campaign["instance"].traffic_group] += float(campaign["instance"].profit)

    for traffic_group in traffic_groups:
        profit[traffic_group] = round(profit[traffic_group], 6)

    return total_revenue, profit


def _calculate_deltas(campaigns_tracker_list, campaigns_db_list, traffic_groups):
    """
    Calculates deltas from previous period. Delta - a profit that relates to the previous period,
    but was not available at the time of calculation.

    :param campaigns_tracker_list: campaigns list for the period with current traffic statistics
    :type campaigns_tracker_list: List[CampaignTracker]

    :param campaigns_db_list: campaigns list for the period with traffic statistics from last report
    :type campaigns_db_list: List[Campaign]

    :param traffic_groups: traffic groups that includes in calculation
    :type traffic_groups: List[str]

    :return: deltas with detailed calculation for the period (split by traffic groups)
    :rtype: Dict[str, List[Union[str, float]]]
    """

    deltas = {traffic_group: ["", 0.0] for traffic_group in traffic_groups}

    for campaign_tracker in campaigns_tracker_list:
        campaign = campaign_tracker["instance"]

        if campaign.traffic_group not in traffic_groups:
            continue

        if campaign in campaigns_db_list:
            campaign_db_profit = [x for x in campaigns_db_list if x.id == campaign.id][0].profit

            if campaign.profit > campaign_db_profit:
                diff = float(campaign.profit - campaign_db_profit)

                if deltas[campaign.traffic_group][1] > 0:
                    deltas[campaign.traffic_group][0] += f" + {diff} [{campaign.id}]"
                else:
                    deltas[campaign.traffic_group][0] = f"{diff} [{campaign.id}]"
                deltas[campaign.traffic_group][1] += diff

    for traffic_group in deltas:
        deltas[traffic_group][1] = round(deltas[traffic_group][1], 6)

        if deltas[traffic_group][1] == 0.0:
            deltas[traffic_group][0] = "0.0"

        elif "+" in deltas[traffic_group][0]:
            deltas[traffic_group][0] = f"{deltas[traffic_group][0]} = " f"{deltas[traffic_group][1]}"

    return deltas


def _calculate_tests(tests_list, campaigns_list, commit, traffic_groups, start_date, end_date):
    """
    Calculates the amount that should be returned to employee (user)
    analyzing the statistics of the test campaigns for the period.

    :param tests_list: list of user tests
    :type tests_list: List[Test]

    :param campaigns_list: list of user campaigns with current statistics
    :type campaigns_list: List[CampaignTracker]

    :param commit: if set to True, than all changes will be committed to database (e.g. tests balances)
    :type commit: bool

    :param traffic_groups: traffic groups that includes in calculation
    :type traffic_groups: List[str]

    :return: amounts with detailed calculation for the period (split by traffic sources)
    :rtype: Dict[str, List[Union[str, float]]]
    """

    tests = {traffic_group: ["", 0.0] for traffic_group in traffic_groups}

    with transaction.atomic():
        for test in tests_list:
            if test.traffic_group not in traffic_groups:
                continue

            test_campaigns_list = []

            test_offers_ids = {offer.id for offer in list(test.offers.all())}
            test_traffic_sources_ids = [ts.id for ts in list(test.traffic_sources.all())]
            test_geos = [geo.country for geo in list(test.geo.all())]

            if len(test_traffic_sources_ids) > 1 and not test.one_budget_for_all_traffic_sources:
                _logger.error(f"Test with id {test.id} doesn't split by traffic sources.")
                raise TestNotSplitError(test_id=test.id)

            if len(test_geos) > 1 and not test.one_budget_for_all_geo:
                _logger.error(f"Test with id {test.id} doesn't split by geo.")
                raise TestNotSplitError(test_id=test.id)

            start_balance = test.balance
            test_balance = test.balance

            for campaign in campaigns_list:
                if (
                        campaign["instance"].traffic_group in traffic_groups
                        and campaign["instance"].traffic_source.id in test_traffic_sources_ids
                        and len(test_offers_ids & set(campaign["offers_list"])) != 0
                ):
                    if test_geos:
                        max_clicks_geo = get_campaign_main_geo(campaign["instance"], start_date, end_date)

                        if max_clicks_geo == -1:
                            raise UpdateError(f"Can't get campaign {campaign.id} main geo.")

                        if max_clicks_geo in test_geos:
                            test_campaigns_list.append(campaign["instance"])
                    else:
                        test_campaigns_list.append(campaign["instance"])

            for test_campaign in test_campaigns_list:
                if test_campaign.profit >= 0:
                    continue

                if test_balance >= 0 > test_balance + test_campaign.profit:
                    if tests[test_campaign.traffic_group][1] > 0:
                        tests[test_campaign.traffic_group][0] += (
                            f" + {round(float(test_balance), 6)} " f"[{test_campaign.id}]"
                        )
                    else:
                        tests[test_campaign.traffic_group][0] += (
                            f"{round(float(test_balance), 6)} " f"[{test_campaign.id}]"
                        )

                    tests[test_campaign.traffic_group][1] += round(float(test_balance), 6)

                elif test_balance + test_campaign.profit >= 0:
                    if tests[test_campaign.traffic_group][1] > 0:
                        tests[test_campaign.traffic_group][0] += (
                            f" + {-round(float(test_campaign.profit), 6)} " f"[{test_campaign.id}]"
                        )
                    else:
                        tests[test_campaign.traffic_group][0] += (
                            f"{-round(float(test_campaign.profit), 6)} " f"[{test_campaign.id}]"
                        )

                    tests[test_campaign.traffic_group][1] -= round(float(test_campaign.profit), 6)

                test_balance += test_campaign.profit

            if commit and (test_balance != start_balance or test_balance <= 0):
                if test_balance > 0:
                    test.balance = test_balance
                    test.save()
                else:
                    test.delete()

    for traffic_group in tests:
        tests[traffic_group][1] = round(tests[traffic_group][1], 6)
        if tests[traffic_group][1] == 0.0:
            tests[traffic_group][0] = "0.0"
        elif "+" in tests[traffic_group][0]:
            tests[traffic_group][0] = f"{tests[traffic_group][0]} = {tests[traffic_group][1]}"

    return tests


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
        profit_with_tests = _calculate_profit_with_tests(dependency.from_user, start_date, end_date, traffic_groups)

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
    :rtype: None
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
    :rtype: None
    """

    with transaction.atomic():
        for campaign in campaigns_to_save:
            if campaign["instance"] not in campaigns_db:
                campaign["instance"].save()

                for offer_id in campaign["offers_list"]:
                    try:
                        offer = Offer.objects.get(id=offer_id)
                    except Offer.DoesNotExist:
                        offers_updated_successfully = update_offers()

                        if offers_updated_successfully:
                            offer = Offer.objects.get(id=offer_id)
                        else:
                            raise UpdateError(message="Can't update offers.")

                    campaign["instance"].offers_list.add(offer)

            campaign["instance"].save()


def _generate_result_table(
        total_revenue,
        final_percent,
        start_balances,
        profits,
        deltas,
        tests,
        from_other_users,
        result,
        user,
        start_date,
        end_date,
):
    if not os.path.exists("media"):
        os.mkdir("media")

    filename = os.path.join("media", f'{uuid4()}.pdf')
    pdf = SimpleDocTemplate(filename, pagesize=landscape(A4), )

    content = [
        Paragraph(f"<b>User:</b> {user}", style=ParagraphStyle(name="style", alignment=1, fontSize=12)),
        Spacer(height=10, width=600),
        Paragraph(f"<b>Period:</b> {start_date} - {end_date}",
                  style=ParagraphStyle(name="style", alignment=1, fontSize=12)),
        Spacer(height=10, width=600),
        Paragraph(f"<b>Total revenue:</b> {total_revenue}",
                  style=ParagraphStyle(name="style", alignment=1, fontSize=12)),
        Spacer(height=10, width=600),
        Paragraph(f"<b>Percent:</b> {final_percent}", style=ParagraphStyle(name="style", alignment=1, fontSize=12)),
        Spacer(height=10, width=600),
    ]

    data = [["--------"] + [traffic_group for traffic_group in result]]

    start_balances_data = ["Start balance"]
    for traffic_group in start_balances:
        if start_balances[traffic_group] > 0:
            start_balances_data.append(Paragraph(f"<font color=green>{start_balances[traffic_group]}</font>",
                                                 style=ParagraphStyle(name="style", alignment=1, fontSize=11)))
        elif start_balances[traffic_group] < 0:
            start_balances_data.append(Paragraph(f"<font color=red>{start_balances[traffic_group]}</font>",
                                                 style=ParagraphStyle(name="style", alignment=1, fontSize=11)))
        else:
            start_balances_data.append(Paragraph(str(start_balances[traffic_group]),
                                                 style=ParagraphStyle(name="style", alignment=1, fontSize=11)))

    data.append(start_balances_data)

    profits_data = ["Profit"]
    for traffic_group in profits:
        if profits[traffic_group] > 0:
            profits_data.append(Paragraph(f"<font color=green>{profits[traffic_group]}</font>",
                                          style=ParagraphStyle(name="style", alignment=1, fontSize=11)))
        elif profits[traffic_group] < 0:
            profits_data.append(Paragraph(f"<font color=red>{profits[traffic_group]}</font>",
                                          style=ParagraphStyle(name="style", alignment=1, fontSize=11)))
        else:
            profits_data.append(Paragraph(str(profits[traffic_group]),
                                          style=ParagraphStyle(name="style", alignment=1, fontSize=11)))

    data.append(profits_data)

    data += [
        ["Previous period"]
        + [Paragraph(deltas[traffic_group][0],
                     style=ParagraphStyle(name="style", alignment=1, fontSize=11, leading=15))
           for traffic_group in deltas],
    ]

    tests_data = ["Tests"]
    for traffic_group in tests:
        count_string = tests[traffic_group][0] \
            .replace(f' = {tests[traffic_group][1]}', f' = <font color=green>{tests[traffic_group][1]}</font>')
        tests_data.append(
            Paragraph(copy(count_string), style=ParagraphStyle(name="style", alignment=1, fontSize=11, leading=15)))

    data.append(tests_data)

    if user.is_lead:
        data.append(
            ["From other users"]
            + [
                Paragraph(from_other_users[traffic_group][0],
                          style=ParagraphStyle(name="style", alignment=1, fontSize=11, leading=15))
                for traffic_group in from_other_users
            ]
        )

    summary_data = ["Summary"]
    for traffic_group in result:
        count_string = result[traffic_group][0]
        if result[traffic_group][1] > 0:
            count_string = count_string \
                .replace(f' = {result[traffic_group][1]}', f' = <font color=green>{result[traffic_group][1]}</font>')
        elif result[traffic_group][1] < 0:
            count_string = count_string \
                .replace(f' = {result[traffic_group][1]}', f' = <font color=red>{result[traffic_group][1]}</font>')
        summary_data.append(
            Paragraph(copy(count_string), style=ParagraphStyle(name="style", alignment=1, fontSize=11, leading=15)))

    data.append(summary_data)

    cols_number = len(result)
    col_widths = [120] + [650 // len(result) for _ in range(cols_number)]
    row_heights = [25, 25, 25, 50, 120]

    if user.is_lead:
        row_heights.append(50)
    row_heights.append(25)

    table = Table(data, colWidths=col_widths, rowHeights=row_heights)

    ts = TableStyle([("GRID", (0, 0), (-1, -1), 2, colors.black), ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                     ('FONTSIZE', (0, 0), (-1, -1), 12), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                     ('LEADING', (0, 0), (-1, -1), 15)])
    table.setStyle(ts)

    pdf.build(
        content
        + [table]
        + [
            Spacer(width=600, height=15),
            Paragraph("© FC Tools 2020", style=ParagraphStyle(name="style", alignment=1, textColor=darkgray)),
        ]
    )

    return filename


def calculate_user_salary(user, start_date, end_date, commit, traffic_groups):
    """
    Calculates user salary for the period from start_date to end_date by selected traffic groups.

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

    :return:
    :rtype: Tuple[
    float,
    float,
    Dict[str, float],
    Dict[str, float],
    Dict[str, List[Union[str, float]]],
    Dict[str, List[Union[str, float]]],
    Optional[Dict[str, List[Union[str, float]]]],
    Dict[str, float],
]
    """

    _logger.info(f"Start salary calculating from {start_date} to {end_date} for user {user}")

    result = _set_start_balances(user, traffic_groups)
    start_balances = deepcopy(result)

    _logger.info("Start balances was successfully set.")

    prev_campaigns_db_list = list(Campaign.objects.filter(user=user))
    prev_campaigns_tracker_list = get_campaigns(start_date - timedelta(days=14), start_date - timedelta(days=1), user)
    current_campaigns_tracker_list = get_campaigns(start_date, end_date, user)

    _logger.info("Successfully get campaigns info (database and tracker, current and previous period).")

    total_revenue, profits = _calculate_profit_for_period(current_campaigns_tracker_list, traffic_groups)

    _logger.info("Total revenue and profits was successfully calculated.")
    _logger.info(f"Total revenue: {total_revenue}")
    _logger.info(f"Profits: {profits}")

    deltas = _calculate_deltas(prev_campaigns_tracker_list, prev_campaigns_db_list, traffic_groups)

    _logger.info(f"Deltas was successfully calculated: {deltas}")

    tests_list = list(Test.objects.filter(user=user))
    tests = _calculate_tests(tests_list, current_campaigns_tracker_list, commit, traffic_groups, start_date, end_date)

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

    report_name = _generate_result_table(
        round(total_revenue, 6),
        final_percent,
        start_balances,
        profits,
        deltas,
        tests,
        from_other_users,
        result,
        user,
        start_date,
        end_date,
    )

    return (round(total_revenue, 6), final_percent, start_balances, profits, deltas, tests, from_other_users, result,
            report_name)
