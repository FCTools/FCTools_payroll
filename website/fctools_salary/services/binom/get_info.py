import os
from decimal import Decimal
from urllib.parse import urlencode

import requests

from fctools_salary.models import (
    User,
    Offer,
    TrafficSource,
    Campaign
)

_api_key = os.environ.get('BINOM_API_KEY')
_requests_url = 'https://fcttrk.com/'


def get_users():
    response = requests.get(_requests_url, params={'page': 'Users', 'api_key': _api_key}).json()

    return [User(id=int(user['id']), login=user['login']) for user in response]


def get_offers():
    response = requests.get(_requests_url, params={'page': 'Offers', 'api_key': _api_key, 'group': 'all',
                                                   'status': 'all'}).json()

    return [Offer(id=int(offer['id']),
                  geo=offer['geo'],
                  name=offer['name'],
                  group=offer['group_name'],
                  network_name=offer['network_name']) for offer in response]


def get_traffic_sources():
    result = []
    all_traffic_sources = requests.get(_requests_url, params={'page': 'Traffic_Sources',
                                                              'api_key': _api_key,
                                                              'status': 'all'}).json()
    all_traffic_sources_count = len(all_traffic_sources)

    for user in User.objects.all():
        response = requests.get(_requests_url, params={'page': 'Traffic_Sources',
                                                       'api_key': _api_key,
                                                       'user_group': user.id,
                                                       'status': 'all'}).json()

        if response and len(response) != all_traffic_sources_count:
            result += [TrafficSource(id=int(ts['id']), name=ts['name'], campaigns=int(ts['camps']),
                                     tokens=1 if int(ts['tokens']) else 0, user=user) for ts in response]

    for ts in all_traffic_sources:
        in_result = False

        for traffic_source in result:
            if traffic_source.id == int(ts['id']):
                in_result = True
                break

        if not in_result:
            result.append(TrafficSource(id=int(ts['id']), name=ts['name'], campaigns=int(ts['camps']),
                                        tokens=1 if int(ts['tokens']) else 0, user=None))

    return result


def get_offers_ids_by_campaign(campaign):
    request_url = _requests_url + 'arm.php'
    result = []

    response = requests.get(request_url, params={'page': 'Campaigns', 'api_key': _api_key,
                                                 'action': 'campaign@get_full', 'id': campaign.id}).json()

    for path in response['routing']['paths']:
        result.extend([int(offer['id_t']) for offer in path['offers']])

    return result


def get_campaigns(start_date, end_date, user):
    params = {
        'page': 'Campaigns',
        'user_group': user.id,
        'date': 12,
        'status': 'all',
        'date_s': str(start_date),
        'date_e': str(end_date),
        'api_key': _api_key
    }
    campaigns_db = list(Campaign.objects.all())

    response = requests.get(_requests_url + '?timezone=+3:00&' + urlencode(params)).json()

    result = [{'campaign': Campaign(id=int(campaign['id']),
                                    name=campaign['name'],
                                    traffic_group=campaign['group_name'],
                                    ts_id_id=int(campaign['ts_id']),
                                    revenue=Decimal(campaign['revenue']),
                                    cost=Decimal(campaign['cost']),
                                    profit=Decimal(campaign['profit']),
                                    user=user), 'offers_list': []} for campaign in response]

    for campaign in result:
        if campaign['campaign'] in campaigns_db:
            for offer in list([x for x in campaigns_db if x.id == campaign['campaign'].id][0].offers_list.all()):
                campaign['offers_list'].append(offer.id)
        else:
            offers_ids = get_offers_ids_by_campaign(campaign['campaign'])
            campaign['offers_list'] = offers_ids

    return result
