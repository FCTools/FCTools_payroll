"""
Copyright © 2020 FC Tools. All rights reserved.
Author: German Yakimov
"""

import json
import logging
from copy import deepcopy
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
from fctools_salary.services.helpers import requests_manager

_logger = logging.getLogger(__name__)


def get_users():
    """
    Get users from tracker.

    :return: list of users
    :rtype: List[User]
    """

    _logger.info("Start getting users from tracker...")

    response = requests_manager.get(
        requests.Session(), settings.TRACKER_URL, params={"page": "Users", "api_key": settings.BINOM_API_KEY}
    )

    if not isinstance(response, requests.Response):
        _logger.error(f"Network error occurred while trying to get users from tracker: {response}")
        return []

    try:
        response_json = response.json()
    except json.JSONDecodeError as decode_error:
        _logger.error(
            f"Can't decode response from tracker (users getting): {decode_error.doc}"
        )
        return []

    try:
        users_list = [User(id=int(user["id"]), login=user["login"]) for user in response_json]
        _logger.info("Users were successfully get.")

        return users_list
    except KeyError:
        _logger.error(f"Can't parse response from tracker (users getting): {response_json}")
        return []


def get_offers():
    """
    Get offers from tracker.

    :return: list of offers
    :rtype: List[Offer]
    """

    _logger.info("Start getting offers from tracker...")

    response = requests_manager.get(
        requests.Session(),
        settings.TRACKER_URL,
        params={"page": "Offers", "api_key": settings.BINOM_API_KEY, "group": "all", "status": "all"},
    )

    if not isinstance(response, requests.Response):
        _logger.error(f"Network error occurred while trying to get offers from tracker: {response}")
        return []

    try:
        response_json = response.json()
    except json.JSONDecodeError as decode_error:
        _logger.error(
            f"Can't decode response from tracker (offers getting): {decode_error.doc}"
        )
        return []

    try:
        offers_list = [
            Offer(
                id=int(offer["id"]),
                geo=offer["geo"],
                name=offer["name"],
                group=offer["group_name"],
                network=offer["network_name"],
            )
            for offer in response_json
        ]
        _logger.info("Offers were successfully get.")

        return offers_list
    except KeyError:
        _logger.error(f"Can't parse response from tracker (offers getting): {response_json}")
        return []


def get_traffic_sources():
    """
    Get traffic sources from tracker.

    :return: list of traffic sources
    :rtype: List[TrafficSource]
    """

    session = requests.Session()
    result = []

    _logger.info("Start getting traffic sources from tracker...")

    all_traffic_sources = requests_manager.get(
        session,
        settings.TRACKER_URL,
        params={"page": "Traffic_Sources", "api_key": settings.BINOM_API_KEY, "status": "all"},
    )

    if not isinstance(all_traffic_sources, requests.Response):
        _logger.error(f"Network error occurred while trying to get traffic_sources from tracker: {all_traffic_sources}")
        return []

    try:
        all_traffic_sources_number = len(all_traffic_sources.json())
    except json.JSONDecodeError as decode_error:
        _logger.error(
            f"Can't decode response from tracker (traffic sources getting): "
            f"{decode_error.doc}"
        )
        return []

    for user in User.objects.all():
        user_traffic_sources = requests_manager.get(
            session,
            settings.TRACKER_URL,
            params={
                "page": "Traffic_Sources",
                "api_key": settings.BINOM_API_KEY,
                "user_group": user.id,
                "status": "all",
            },
        )

        if not isinstance(user_traffic_sources, requests.Response):
            _logger.error(
                f"Network error occurred while trying to get traffic sources from tracker: {user_traffic_sources}")
            continue

        try:
            user_traffic_sources_json = user_traffic_sources.json()
        except json.JSONDecodeError as decode_error:
            _logger.error(
                f"Can't decode response from tracker (traffic sources getting): "
                f"{decode_error.doc}"
            )
            return []

        if user_traffic_sources_json and len(user_traffic_sources_json) != all_traffic_sources_number:
            try:
                result += [
                    TrafficSource(
                        id=int(traffic_source["id"]),
                        name=traffic_source["name"],
                        campaigns=int(traffic_source["camps"]),
                        tokens=1 if int(traffic_source["tokens"]) else 0,
                        user=user,
                    )
                    for traffic_source in user_traffic_sources_json
                ]
            except KeyError:
                _logger.error(
                    f"Can't parse response from tracker (traffic sources getting): {user_traffic_sources_json}")
                return []

    _logger.info("Traffic sources were successfully get.")
    return result


def get_offers_ids_by_campaign(campaign):
    """
    Get list of offers ids for taken campaign.

    :param campaign: campaign
    :type campaign: Campaign

    :return: list of of offers ids
    :rtype: List[int]
    """

    result = []

    requests_url = settings.TRACKER_URL + "arm.php"
    response = requests_manager.get(
        requests.Session(),
        requests_url,
        params={
            "page": "Campaigns",
            "api_key": settings.BINOM_API_KEY,
            "action": "campaign@get_full",
            "id": campaign.id,
        },
    )

    if not isinstance(response, requests.Response):
        _logger.error(f"Network error occurred while trying to get campaign full info from tracker: {response}")
        return []

    try:
        response_json = response.json()
    except json.JSONDecodeError as decode_error:
        _logger.error(
            f"Can't decode response from tracker (getting campaign full info): "
            f"{decode_error.doc}"
        )
        return []

    try:
        for path in response_json["routing"]["paths"]:
            result += [int(offer["id_t"]) for offer in path["offers"]]
    except KeyError:
        _logger.error(f"Can't parse response from tracker (getting offers ids by campaign): {response_json}")
        return []

    return result


def get_campaigns(start_date, end_date, user, redis_server=None):
    """
    Get user campaigns from start_date to end_date.

    :param start_date: period start date
    :type start_date: date

    :param end_date: period end date
    :type end_date: date

    :param user: user
    :type user: User

    :param redis_server: RedisClient instance for caching
    :type redis_server: RedisClient

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

    campaigns_db_ids = [campaign.id for campaign in
                        list(Campaign.objects.filter(user_id=user.id).prefetch_related('offers_list'))]

    _logger.info(f"Start getting campaigns from {start_date} to {end_date} for user {user}")

    campaigns_tracker = requests_manager.get(
        requests.Session(), f"{settings.TRACKER_URL}?timezone=+3:00&{urlencode(params)}"
    )

    if not isinstance(campaigns_tracker, requests.Response):
        _logger.error(
            f"Network error occurred while trying to get campaign full info from tracker: {campaigns_tracker}")
        return []

    try:
        campaigns_tracker_json = campaigns_tracker.json()
    except json.JSONDecodeError as decode_error:
        _logger.error(
            f"Can't decode response from tracker (getting info about campaigns): "
            f"{decode_error.doc}"
        )
        return []

    try:
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
            for campaign in campaigns_tracker_json
        ]
    except KeyError:
        _logger.error(f"Can't parse response from tracker (campaigns getting): {campaigns_tracker_json}")
        return []

    for campaign in result:
        if redis_server:
            if not redis_server.exists(campaign["instance"].id):
                if campaign["instance"].id in campaigns_db_ids:
                    offers_ids = [offer.id for offer in
                                  Campaign.objects.get(id__exact=campaign["instance"].id).offers_list.all()]

                else:
                    offers_ids = get_offers_ids_by_campaign(campaign["instance"])

                redis_server.add_campaign_offers(campaign["instance"].id, offers_ids)
            else:
                offers_ids = redis_server.get_campaign_offers(campaign["instance"].id)
        else:
            if campaign["instance"].id in campaigns_db_ids:
                offers_ids = [offer.id for offer in
                              Campaign.objects.get(id__exact=campaign["instance"].id).offers_list.all()]

            else:
                offers_ids = get_offers_ids_by_campaign(campaign["instance"])

        # if not offers_ids:
        #     return []

        campaign["offers_list"] = deepcopy(offers_ids)

    _logger.info(f"Campaigns for {user} from {start_date} to {end_date} were successfully get.")
    return result


def get_campaign_main_geo(campaign, start_date, end_date):
    """
    Get campaign's geo statistics and finds main geo (max clicks geo) based on period.

    :param campaign: campaign
    :type campaign: Campaign

    :param start_date: period start date
    :type start_date: date

    :param end_date: period end date
    :type end_date: date

    :return: main geo for this campaign, if success, else -1
    :rtype: Union[int, str]
    """

    campaign_geos = []

    params = urlencode(
        {
            "page": "Stats",
            "camp_id": campaign.id,
            "api_key": settings.BINOM_API_KEY,
            "group1": 19,
            "group2": 1,
            "group3": 1,
            "date": 12,
            "date_s": str(start_date),
            "date_e": str(end_date),
        }
    )

    campaign_statistics = requests_manager.get(requests.Session(), f"{settings.TRACKER_URL}?{params}&timezone=+3:00")

    if not isinstance(campaign_statistics, requests.Response):
        _logger.error(
            f"Network error occurred while trying to get campaign statistics from tracker: {campaign_statistics}")
        return -1

    try:
        campaign_statistics_json = campaign_statistics.json()
    except json.JSONDecodeError as decode_error:
        _logger.error(f"Can't decode response from tracker (campaigns getting): {decode_error.doc}")
        return -1

    try:
        if campaign_statistics_json != "no clicks":
            for geo in campaign_statistics_json:
                campaign_geos.append({"country": geo["name"], "clicks": int(geo["clicks"])})

            max_clicks_geo = max(campaign_geos, key=lambda x: x["clicks"])["country"]
            return max_clicks_geo
        else:
            return None
    except TypeError:
        _logger.warning(f"Can't get campaign main geo, campaign id: {campaign.id}. Maybe, this campaign is empty?")
        return None
