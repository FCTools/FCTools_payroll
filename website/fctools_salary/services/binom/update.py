from fctools_salary.models import User, Offer, TrafficSource

from .get_info import get_users, get_offers, get_traffic_sources


def _update_users():
    users_db = User.objects.all()
    users_tracker = get_users()

    for user in users_tracker:
        if user not in users_db:
            user.save()


def _update_offers():
    offers_db = Offer.objects.all()
    offers_tracker = get_offers()

    for offer in offers_tracker:
        if offer not in offers_db:
            offer.save()


def _update_traffic_sources():
    traffic_sources_db = TrafficSource.objects.all()
    traffic_sources_tracker = get_traffic_sources()

    for ts in traffic_sources_tracker:
        if ts not in traffic_sources_db:
            ts.save()


def update_basic_info():
    _update_users()
    _update_traffic_sources()
    _update_offers()
