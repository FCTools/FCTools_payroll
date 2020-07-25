import logging

from django.db import transaction

from fctools_salary.domains.tracker.offer import Offer
from fctools_salary.domains.tracker.traffic_source import TrafficSource
from fctools_salary.domains.accounts.user import User
from .get_info import get_users, get_offers, get_traffic_sources


_logger = logging.getLogger(__name__)


def _update_users():
    """
    Synchronize Users table in tracker and database.

    :return: None
    """

    _logger.info("Start to sync users.")

    users_db = User.objects.all()
    users_tracker = get_users()

    with transaction.atomic():
        for user in users_tracker:
            if user not in users_db:
                user.save()

    _logger.info("Users syncing was successful.")


def update_offers():
    """
    Synchronize Offers table in tracker and database.

    :return: None
    """

    _logger.info("Start to sync offers.")

    offers_db = Offer.objects.all()
    offers_tracker = get_offers()

    with transaction.atomic():
        for offer in offers_tracker:
            if offer not in offers_db:
                offer.save()

    _logger.info("Offers syncing was successful.")


def _update_traffic_sources():
    """
    Synchronize TrafficSources table in tracker and database.

    :return: None
    """

    _logger.info("Start to sync traffic sources.")

    traffic_sources_db = TrafficSource.objects.all()
    traffic_sources_tracker = get_traffic_sources()

    with transaction.atomic():
        for ts in traffic_sources_tracker:
            if ts not in traffic_sources_db:
                ts.save()

    _logger.info("Traffic sources syncing was successful.")


def update_basic_info():
    """
    Synchronize Users, Offers and TrafficSources tables in tracker and database.

    :return: None
    """

    _logger.info("Start to sync database and tracker.")

    _update_users()
    _update_traffic_sources()
    update_offers()

    _logger.info("Syncing was successful.")
