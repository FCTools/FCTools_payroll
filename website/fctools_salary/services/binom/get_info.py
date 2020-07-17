import os
from datetime import date
from decimal import Decimal
from typing import List, Dict
from urllib.parse import urlencode

import requests

from fctools_salary.domains.tracker.campaign import Campaign
from fctools_salary.domains.tracker.offer import Offer
from fctools_salary.domains.tracker.traffic_source import TrafficSource
from fctools_salary.domains.accounts.user import User

_binom_api_key = os.environ.get("BINOM_API_KEY")
_tracker_url = "https://fcttrk.com/"


def get_users():
    """
    Gets users from tracker.

    :return: list of users
    :rtype: List[User]
    """

    response = requests.get(_tracker_url, params={"page": "Users", "api_key": _binom_api_key}).json()
    return [User(id=int(user["id"]), login=user["login"]) for user in response]


def get_offers():
    """
    Gets offers from tracker.

    :return: list of offers
    :rtype: List[Offer]
    """

    response = requests.get(
        _tracker_url, params={"page": "Offers", "api_key": _binom_api_key, "group": "all", "status": "all"}
    ).json()

    return [
        Offer(
            id=int(offer["id"]),
            geo=offer["geo"],
            name=offer["name"],
            group=offer["group_name"],
            network=offer["network_name"],
        )
        for offer in response
    ]


def get_traffic_sources():
    """
    Gets traffic sources from tracker.

    :return: list of traffic sources
    :rtype: List[TrafficSource]
    """

    result = []
    all_traffic_sources = requests.get(
        _tracker_url, params={"page": "Traffic_Sources", "api_key": _binom_api_key, "status": "all"}
    ).json()
    all_traffic_sources_number = len(all_traffic_sources)

    for user in User.objects.all():
        user_traffic_sources = requests.get(
            _tracker_url,
            params={"page": "Traffic_Sources", "api_key": _binom_api_key, "user_group": user.id, "status": "all"},
        ).json()

        if user_traffic_sources and len(user_traffic_sources) != all_traffic_sources_number:
            result += [
                TrafficSource(
                    id=int(traffic_source["id"]),
                    name=traffic_source["name"],
                    campaigns=int(traffic_source["camps"]),
                    tokens=1 if int(traffic_source["tokens"]) else 0,
                    user=user,
                )
                for traffic_source in user_traffic_sources
            ]

    return result


def get_offers_ids_by_campaign(campaign: Campaign):
    """
    Gets list of offers ids for taken campaign.

    :param campaign: campaign
    :type campaign: Campaign

    :return: list of of offers ids
    :rtype: List[int]
    """

    result = []

    requests_url = _tracker_url + "arm.php"
    response = requests.get(
        requests_url,
        params={"page": "Campaigns", "api_key": _binom_api_key, "action": "campaign@get_full", "id": campaign.id},
    ).json()

    for path in response["routing"]["paths"]:
        result += [int(offer["id_t"]) for offer in path["offers"]]

    return result


def get_campaigns(start_date, end_date, user):
    """
    Gets user campaigns from start_date to end_date.

    :param start_date: period start date
    :type start_date: date

    :param end_date: period end date
    :type end_date: date

    :param user: user
    :type user: User

    :return: list of campaigns from tracker, each campaign is dict with 2 keys: instance - Campaign class instance
    from models, offers_list - list of offers ids
    :rtype: List[Dict[str, Union[CampaignTracker, List]]]
    """

    params = {
        "page": "Campaigns",
        "user_group": user.id,
        "date": 12,
        "status": "all",
        "date_s": str(start_date),
        "date_e": str(end_date),
        "api_key": _binom_api_key,
    }

    campaigns_db = list(Campaign.objects.all())
    campaigns_tracker = requests.get(f"{_tracker_url}?timezone=+3:00&{urlencode(params)}").json()

    result = [
        {
            "instance": Campaign(
                id=int(campaign["id"]),
                name=campaign["name"],
                traffic_group=campaign["group_name"],
                traffic_source_id=int(campaign["ts_id"]),
                revenue=Decimal(campaign["revenue"]),
                cost=Decimal(campaign["cost"]),
                profit=Decimal(campaign["profit"]),
                user=user,
            ),
            "offers_list": [],
        }
        for campaign in campaigns_tracker
    ]

    for campaign in result:
        if campaign["instance"] in campaigns_db:
            for offer in list([x for x in campaigns_db if x.id == campaign["instance"].id][0].offers_list.all()):
                campaign["offers_list"].append(offer.id)
        else:
            offers_ids = get_offers_ids_by_campaign(campaign["instance"])
            campaign["offers_list"] = offers_ids

    return result
