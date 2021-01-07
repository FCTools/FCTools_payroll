"""
Copyright © 2020-2021 FC Tools.
All rights reserved.
Author: German Yakimov
"""

import json

import redis
from django.conf import settings


class RedisClient:
    def __init__(self):
        self._server = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT)

    def add_campaign_main_geo(self, campaign_id, main_geo):
        campaign_id = str(campaign_id)
        if not self._server.exists(campaign_id):
            self._server.append(str(campaign_id), json.dumps({'geo': main_geo}))

    def exists(self, campaign_id):
        campaign_id = str(campaign_id)

        return self._server.exists(campaign_id)

    def get_campaign_main_geo(self, campaign_id):
        campaign_id = str(campaign_id)

        if self.exists(campaign_id):
            return json.loads(self._server.get(campaign_id))['geo']

    def get_campaign_offers(self, campaign_id):
        campaign_id = str(campaign_id)

        if self.exists(campaign_id):
            return json.loads(self._server.get(campaign_id))['offers']

    def add_campaign_offers(self, campaign_id, offers_list):
        campaign_id = str(campaign_id)

        if not self.exists(campaign_id):
            self._server.append(campaign_id, json.dumps({'offers': offers_list}))

    def clear(self):
        self._server.flushdb()

    def __del__(self):
        self._server.flushdb()
        self._server.close()
