import json
import logging
from datetime import date
from decimal import Decimal
from typing import List, Dict
from urllib.parse import urlencode

import requests
from django.conf import settings

from fctools_salary.domains.accounts.user import User
from fctools_salary.domains.tracker.campaign import Campaign
from fctools_salary.domains.tracker.offer import Offer
from fctools_salary.domains.tracker.traffic_source import TrafficSource
from fctools_salary.services import requests_manager

_logger = logging.getLogger(__name__)


def get_users():
    """
    Gets users from tracker.

    :return: list of users
    :rtype: List[User]
    """

    _logger.info('Start getting users from tracker...')

    response = requests_manager.get(requests.Session(), settings.TRACKER_URL,
                                    params={"page": "Users", "api_key": settings.BINOM_API_KEY})

    if not isinstance(response, requests.Response):
        _logger.error(f"Error occurred while trying to get users from tracker: {response}")
        return []

    try:
        return [User(id=int(user["id"]), login=user["login"]) for user in response.json()]
    except json.JSONDecodeError as decode_error:
        _logger.error(
            f'Error occurred while trying to decode response from tracker (users updating): {decode_error.doc}')
        return []


def get_offers():
    """
    Gets offers from tracker.

    :return: list of offers
    :rtype: List[Offer]
    """

    _logger.info("Start getting offers from tracker...")

    response = requests_manager.get(requests.Session(),
                                    settings.TRACKER_URL,
                                    params={"page": "Offers", "api_key": settings.BINOM_API_KEY, "group": "all",
                                            "status": "all"},
                                    )

    if not isinstance(response, requests.Response):
        _logger.error(f"Error occurred while trying to get offers from tracker: {response}")
        return []

    try:
        return [
            Offer(
                id=int(offer["id"]),
                geo=offer["geo"],
                name=offer["name"],
                group=offer["group_name"],
                network=offer["network_name"],
            )
            for offer in response.json()
        ]
    except json.JSONDecodeError as decode_error:
        _logger.error(
            f'Error occurred while trying to decode response from tracker (offers updating): {decode_error.doc}')
        return []


def get_traffic_sources():
    """
    Gets traffic sources from tracker.

    :return: list of traffic sources
    :rtype: List[TrafficSource]
    """

    session = requests.Session()

    result = []

    _logger.info("Start getting traffic sources from tracker...")

    all_traffic_sources = requests_manager.get(session,
                                               settings.TRACKER_URL,
                                               params={"page": "Traffic_Sources", "api_key": settings.BINOM_API_KEY,
                                                       "status": "all"}
                                               )

    if not isinstance(all_traffic_sources, requests.Response):
        _logger.error(f"Error occurred while trying to get traffic_sources from tracker: {all_traffic_sources}")
        return []

    try:
        all_traffic_sources_number = len(all_traffic_sources.json())
    except json.JSONDecodeError as decode_error:
        _logger.error(
            f'Error occurred while trying to decode response from tracker (traffic sources updating): '
            f'{decode_error.doc}')
        return []

    for user in User.objects.all():
        user_traffic_sources = requests_manager.get(session,
                                                    settings.TRACKER_URL,
                                                    params={
                                                        "page": "Traffic_Sources",
                                                        "api_key": settings.BINOM_API_KEY,
                                                        "user_group": user.id,
                                                        "status": "all",
                                                    },
                                                    )

        if not isinstance(user_traffic_sources, requests.Response):
            _logger.error(f"Error occurred while trying to get traffic sources from tracker: {user_traffic_sources}")
            continue

        try:
            user_traffic_sources = user_traffic_sources.json()
        except json.JSONDecodeError as decode_error:
            _logger.error(
                f'Error occurred while trying to decode response from tracker (traffic sources updating): '
                f'{decode_error.doc}')
            return []

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

    requests_url = settings.TRACKER_URL + "arm.php"
    response = requests_manager.get(requests.Session(),
                                    requests_url,
                                    params={
                                        "page": "Campaigns",
                                        "api_key": settings.BINOM_API_KEY,
                                        "action": "campaign@get_full",
                                        "id": campaign.id,
                                    },
                                    )

    if not isinstance(response, requests.Response):
        _logger.error(f"Error occurred while trying to get campaign full info from tracker: {response}")
        return []

    try:
        response = response.json()
    except json.JSONDecodeError as decode_error:
        _logger.error(
            f'Error occurred while trying to decode response from tracker (getting campaign full info): '
            f'{decode_error.doc}')
        return []

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
        "api_key": settings.BINOM_API_KEY,
    }

    campaigns_db = list(Campaign.objects.all())

    _logger.info(f"Start getting campaigns from {start_date} to {end_date} for user {user}")

    campaigns_tracker = requests_manager.get(requests.Session(), f"{settings.TRACKER_URL}?timezone=+3:00&{urlencode(params)}")

    if not isinstance(campaigns_tracker, requests.Response):
        _logger.error(f"Error occurred while trying to get campaign full info from tracker: {campaigns_tracker}")
        return []

    try:
        campaigns_tracker = campaigns_tracker.json()
    except json.JSONDecodeError as decode_error:
        _logger.error(
            f'Error occurred while trying to decode response from tracker (getting info about campaigns): '
            f'{decode_error.doc}')
        return []

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

            if not offers_ids:
                return []

            campaign["offers_list"] = offers_ids

    return result
