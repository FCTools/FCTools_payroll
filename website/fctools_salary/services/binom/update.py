import logging

from django.db import transaction

from fctools_salary.domains.tracker.offer import Offer
from fctools_salary.domains.tracker.traffic_source import TrafficSource
from fctools_salary.domains.accounts.user import User
from fctools_salary.exceptions import UpdateError
from .get_info import get_users, get_offers, get_traffic_sources


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
        return False

    with transaction.atomic():
        for user in users_tracker:
            if user not in users_db:
                user.save()

    _logger.info("Users syncing was successful.")
    return True


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
        return False

    with transaction.atomic():
        for offer in offers_tracker:
            if offer not in offers_db:
                offer.save()

    _logger.info("Offers syncing was successful.")
    return True


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
        return False

    with transaction.atomic():
        for ts in traffic_sources_tracker:
            if ts not in traffic_sources_db:
                ts.save()

    _logger.info("Traffic sources syncing was successful.")
    return True


def update_basic_info():
    """
    Synchronize users, offers and traffic sources tables in tracker with database.

    :return: None
    """

    _logger.info("Start to sync database and tracker.")

    users_updated_successfully = _update_users()
    traffic_sources_updated_successfully = _update_traffic_sources()
    offers_updated_successfully = update_offers()

    if users_updated_successfully and traffic_sources_updated_successfully and offers_updated_successfully:
        _logger.info("Syncing was successful.")
    else:
        raise UpdateError(message="Can't sync database with tracker.")
