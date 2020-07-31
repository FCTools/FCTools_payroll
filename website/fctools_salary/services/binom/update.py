"""
Copyright © 2020 FC Tools. All rights reserved.
Author: German Yakimov
"""

import logging

from django.db import transaction

from fctools_salary.domains.tracker.offer import Offer
from fctools_salary.domains.tracker.traffic_source import TrafficSource
from fctools_salary.domains.accounts.user import User
from fctools_salary.exceptions import UpdateError
from fctools_salary.services.binom.get_info import get_users, get_offers, get_traffic_sources


_logger = logging.getLogger(__name__)


def _update_users():
    """
    Synchronize users table in tracker with database.

    :return: status (True/False)
    :rtype: bool
    """

    _logger.info("Start to sync users.")

    users_db = User.objects.all()
    users_tracker = get_users()

    if not users_tracker:
        _logger.error("Can't get users from tracker.")
        raise UpdateError(message="Can't sync users from tracker.")

    with transaction.atomic():
        for user in users_tracker:
            if user not in users_db:
                user.save()

    _logger.info("Users syncing was successful.")


def update_offers():
    """
    Synchronize offers table in tracker with database.

    :return: status (True/False)
    :rtype: bool
    """

    _logger.info("Start to sync offers.")

    offers_db = Offer.objects.all()
    offers_tracker = get_offers()

    if not offers_tracker:
        _logger.error("Can't get offers from tracker.")
        raise UpdateError(message="Can't sync offers from tracker.")

    with transaction.atomic():
        for offer in offers_tracker:
            if offer not in offers_db:
                offer.save()

    _logger.info("Offers syncing was successful.")


def _update_traffic_sources():
    """
    Synchronize traffic sources table in tracker with database.

    :return: status (True/False)
    :rtype: bool
    """

    _logger.info("Start to sync traffic sources.")

    traffic_sources_db = TrafficSource.objects.all()
    traffic_sources_tracker = get_traffic_sources()

    if not traffic_sources_tracker:
        _logger.error("Can't get traffic sources from tracker.")
        raise UpdateError(message="Can't sync traffic sources from tracker.")

    with transaction.atomic():
        for ts in traffic_sources_tracker:
            if ts not in traffic_sources_db:
                ts.save()

    _logger.info("Traffic sources syncing was successful.")


def update_basic_info():
    """
    Synchronize users, offers and traffic sources tables in tracker with database.

    :return: None
    """

    _logger.info("Start to sync database and tracker.")

    _update_users()
    _update_traffic_sources()
    update_offers()

    _logger.info("Syncing was successful.")
