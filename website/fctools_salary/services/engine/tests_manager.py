# Copyright © 2020-2021 Filthy Claws Tools - All Rights Reserved
#
# This file is part of FCTools_payroll
#
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Author: German Yakimov <german13yakimov@gmail.com>

import decimal
import logging
from datetime import datetime, timedelta

from django.db import transaction

from fctools_salary.domains.accounts.test import Test
from fctools_salary.exceptions import UpdateError, TestNotSplitError
from fctools_salary.services.binom.get_info import get_campaigns, get_campaign_main_geo, get_profit_by_particular_offer
from fctools_salary.services.engine.tracker_manager import TrackerManager
from fctools_salary.services.helpers.redis_client import RedisClient

_logger = logging.getLogger(__name__)


class TestsManager:
    """
    Service for test tasks managing.
    """

    @staticmethod
    def calculate_tests(tests_list, campaigns_list, commit, traffic_groups, start_date, end_date):
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

        :param start_date: period start date
        :type start_date: date

        :param end_date: period end date
        :type end_date: date

        :return: amounts with detailed calculation for the period (split by traffic sources)
        :rtype: Dict[str, List[Union[str, float]]]
        """

        tests = {traffic_group: ["", 0.0] for traffic_group in traffic_groups}
        done_campaigns_ids = set()
        redis = RedisClient()

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

                if len(test_offers_ids) > 1 and not test.one_budget_for_all_offers:
                    _logger.error(f"Test with id {test.id} doesn't split by offers.")
                    raise TestNotSplitError(test_id=test.id)

                start_balance = test.balance
                test_balance = test.balance

                for campaign in campaigns_list:
                    if campaign["instance"].id in done_campaigns_ids:
                        continue

                    if (
                            campaign["instance"].traffic_group in traffic_groups
                            and campaign["instance"].traffic_source.id in test_traffic_sources_ids
                            and len(test_offers_ids & set(campaign["offers_list"])) != 0
                    ):
                        test_offers_list = list(test_offers_ids & set(campaign["offers_list"]))

                        if not test_geos:
                            campaign['instance'].profit = decimal.Decimal(0)

                        for test_offer_id in test_offers_list:
                            if test_geos:
                                if not redis.exists(campaign["instance"].id):
                                    max_clicks_geo = get_campaign_main_geo(campaign["instance"], start_date, end_date)
                                    redis.add_campaign_main_geo(campaign["instance"].id, max_clicks_geo)
                                else:
                                    max_clicks_geo = redis.get_campaign_main_geo(campaign["instance"].id)

                                if max_clicks_geo == -1:
                                    raise UpdateError(f"Can't get campaign {campaign.id} main geo.")

                                if max_clicks_geo in test_geos:
                                    test_campaigns_list.append(campaign["instance"])
                            else:
                                profit = get_profit_by_particular_offer(campaign['instance'].id,
                                                                        test_offer_id, start_date,
                                                                        end_date)

                                if profit is None:
                                    return

                            # set profit to profit only by test offers
                            campaign['instance'].profit += decimal.Decimal(profit)

                        test_campaigns_list.append(campaign['instance'])

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
                    done_campaigns_ids.add(test_campaign.id)

                if commit and (test_balance != start_balance or test_balance <= 0):
                    if test_balance > 0:
                        test.balance = test_balance
                        test.save()
                    else:
                        test.balance = 0.0
                        test.archived = True
                        test.save()

        redis.clear()

        for traffic_group in tests:
            tests[traffic_group][1] = round(tests[traffic_group][1], 6)
            if tests[traffic_group][1] == 0.0:
                tests[traffic_group][0] = "0.0"
            elif "+" in tests[traffic_group][0]:
                tests[traffic_group][0] = f"{tests[traffic_group][0]} = {tests[traffic_group][1]}"

        return tests

    @staticmethod
    def calculate_profit_with_tests(user, start_date, end_date, traffic_groups):
        """
        Calculates user profit for the period including tests

        :param user: user
        :type user: User

        :param start_date: date
        :type start_date: date

        :param end_date: date
        :type end_date: date

        :param traffic_groups: traffic groups to calculate
        :type traffic_groups: List[str]

        :return user profit from start_date to end_date including tests
        :rtype: Dict[str, float]
        """

        result = {traffic_group: 0.0 for traffic_group in traffic_groups}

        current_campaigns_tracker = get_campaigns(start_date, end_date, user)

        if not current_campaigns_tracker:
            raise UpdateError(message=f"Can't get campaigns from {start_date} to {end_date} for user {user}")

        profit = TrackerManager.calculate_profit_for_period(current_campaigns_tracker, traffic_groups)[1]

        tests_list = list(Test.objects.filter(user=user, archived=False))
        tests = TestsManager.calculate_tests(tests_list, current_campaigns_tracker, False, traffic_groups, start_date,
                                             end_date)

        for traffic_group in result:
            result[traffic_group] += profit[traffic_group] + tests[traffic_group][1]

        return result

    @staticmethod
    def archive_user_tests(user):
        tests_list = Test.objects.filter(user=user, archived=False)
        today = datetime.utcnow().date()

        with transaction.atomic():
            for test in tests_list:
                if today - test.adding_date >= timedelta(days=test.lifetime):
                    test.archived = True
                    test.save()
