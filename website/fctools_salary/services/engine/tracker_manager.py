"""
Copyright © 2020 FC Tools. All rights reserved.
Author: German Yakimov
"""

from fctools_salary.models import Report
from fctools_salary.services.binom.get_info import get_campaigns
from fctools_salary.services.helpers.redis_client import RedisClient


class TrackerManager:
    """
    Service for calculations based on info from tracker.
    """

    @staticmethod
    def calculate_profit_for_period(campaigns_list, traffic_groups):
        """
        Calculates user's revenue and profit for the period without tests (just adds profit for all user campaigns).

        :param campaigns_list: list of campaigns for period with current traffic statistics
        :type campaigns_list: List[CampaignTracker]

        :param traffic_groups: traffic groups that includes in calculation
        :type traffic_groups: List[str]

        :return: total revenue and profit for this period (split by traffic groups)
        :rtype: Tuple[float, Dict[str, float]]
        """

        profits = {traffic_group: 0.0 for traffic_group in traffic_groups}
        revenues = {traffic_group: 0.0 for traffic_group in traffic_groups}

        for campaign in campaigns_list:
            if campaign["instance"].traffic_group in traffic_groups:
                profits[campaign["instance"].traffic_group] += float(campaign["instance"].profit)
                revenues[campaign["instance"].traffic_group] += float(campaign["instance"].revenue)

        for traffic_group in traffic_groups:
            profits[traffic_group] = round(profits[traffic_group], 6)
            revenues[traffic_group] = round(revenues[traffic_group], 6)

        return revenues, profits

    @staticmethod
    def calculate_deltas(user, traffic_groups, commit):
        """
        Calculates deltas from previous period. Delta - a profit that relates to the previous periods,
        but was not available at the time of calculation.

        :param traffic_groups: traffic groups that includes in calculation
        :type traffic_groups: List[str]

        :param user: user
        :type user: User

        :param commit: save changes to database
        :type commit: bool

        :return: deltas for last 6 periods (split by traffic groups)
        :rtype: Dict[str, List[Union[str, float]]]
        """

        deltas = {traffic_group: {} for traffic_group in traffic_groups}

        reports_list = Report.objects.filter(user=user)

        redis = RedisClient()

        for report in reports_list:
            key = f'{report.start_date} - {report.end_date}'
            campaigns = get_campaigns(report.start_date, report.end_date, user, redis)
            profits = TrackerManager.calculate_profit_for_period(campaigns, traffic_groups)[1]

            if "ADMIN" in traffic_groups and report.profit_admin:
                if float(report.profit_admin) < profits["ADMIN"]:
                    deltas["ADMIN"][key] = profits["ADMIN"] - float(report.profit_admin)

            if "PUSH traff" in traffic_groups and report.profit_push:
                if float(report.profit_push) < profits["PUSH traff"]:
                    deltas["PUSH traff"][key] = profits["PUSH traff"] - float(report.profit_push)

            if "POP traff" in traffic_groups and report.profit_pop:
                if float(report.profit_pop) < profits["POP traff"]:
                    deltas["POP traff"][key] = profits["POP traff"] - float(report.profit_pop)

            if "NATIVE traff" in traffic_groups and report.profit_native:
                if float(report.profit_native) < profits["NATIVE traff"]:
                    deltas["NATIVE traff"][key] = profits["NATIVE traff"] - float(report.profit_native)

            if "FPA/HSA/PWA" in traffic_groups and report.profit_fpa_hsa_pwa:
                if float(report.profit_fpa_hsa_pwa) < profits["FPA/HSA/PWA"]:
                    deltas["FPA/HSA/PWA"][key] = profits["FPA/HSA/PWA"] - float(report.profit_fpa_hsa_pwa)

            if "INAPP traff" in traffic_groups and report.profit_inapp:
                if float(report.profit_inapp) < profits["INAPP traff"]:
                    deltas["INAPP traff"][key] = profits["INAPP traff"] - float(report.profit_inapp)

            if "Tik Tok" in traffic_groups and report.profit_tik_tok:
                if float(report.profit_tik_tok) < profits["Tik Tok"]:
                    deltas["Tik Tok"][key] = profits["Tik Tok"] - float(report.profit_tik_tok)

            if commit:
                if "INAPP traff" in traffic_groups:
                    report.profit_inapp = profits["INAPP traff"]
                if "FPA/HSA/PWA" in traffic_groups:
                    report.profit_fpa_hsa_pwa = profits["FPA/HSA/PWA"]
                if "NATIVE traff" in traffic_groups:
                    report.profit_native = profits["NATIVE traff"]
                if "POP traff" in traffic_groups:
                    report.profit_pop = profits["POP traff"]
                if "ADMIN" in traffic_groups:
                    report.profit_admin = profits["ADMIN"]
                if "PUSH traff" in traffic_groups:
                    report.profit_push = profits["PUSH traff"]
                if "Tik Tok" in traffic_groups:
                    report.profit_tik_tok = profits["Tik Tok"]

                report.save()

        redis.clear()

        for traffic_group in deltas:
            for key in deltas[traffic_group]:
                deltas[traffic_group][key] = round(deltas[traffic_group][key], 6)

        return deltas
