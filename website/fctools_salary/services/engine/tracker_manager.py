"""
Copyright © 2020 FC Tools. All rights reserved.
Author: German Yakimov
"""


class TrackerManager:
    """
    Service for calculations based on info from tracker.
    """

    @staticmethod
    def calculate_profit_for_period(campaigns_list, traffic_groups):
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

    @staticmethod
    def calculate_deltas(campaigns_tracker_list, campaigns_db_list, traffic_groups):
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
