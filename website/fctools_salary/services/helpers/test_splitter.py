"""
Copyright © 2020-2021 FC Tools.
All rights reserved.
Author: German Yakimov
"""

from fctools_salary.domains.accounts.test import Test


class TestSplitter:
    def __init(self):
        pass

    def split(self, test):
        test_offers = list(test.offers.all())
        test_traffic_sources = list(test.traffic_sources.all())
        test_geo = list(test.geo.all())

        if not test.one_budget_for_all_offers and len(test_offers) > 1:
            tests_by_offers = self.split_by_offers(test)
            test.delete()

            for test in tests_by_offers:
                self.split(test)

        elif not test.one_budget_for_all_traffic_sources and len(test_traffic_sources) > 1:
            tests_by_ts = self.split_by_traffic_sources(test)
            test.delete()

            for test in tests_by_ts:
                self.split(test)

        elif not test.one_budget_for_all_geo and len(test_geo) > 1:
            self.split_by_geo(test)
            test.delete()

    @staticmethod
    def split_by_offers(test):
        result = []

        test_offers = list(test.offers.all())
        test_traffic_sources = list(test.traffic_sources.all())
        test_geo = list(test.geo.all())

        for offer in test_offers:
            new_test = Test(budget=test.budget, user=test.user,
                            one_budget_for_all_traffic_sources=test.one_budget_for_all_traffic_sources,
                            traffic_group=test.traffic_group,
                            balance=test.balance,
                            one_budget_for_all_geo=test.one_budget_for_all_geo,
                            adding_date=test.adding_date,
                            lifetime=test.lifetime,
                            archived=test.archived)
            new_test.save()

            for ts in test_traffic_sources:
                new_test.traffic_sources.add(ts)

            for geo in test_geo:
                new_test.geo.add(geo)

            new_test.offers.add(offer)
            result.append(new_test)

        return result

    @staticmethod
    def split_by_geo(test):
        result = []

        test_offers = list(test.offers.all())
        test_traffic_sources = list(test.traffic_sources.all())
        test_geo = list(test.geo.all())

        for geo in test_geo:
            new_test = Test(budget=test.budget, user=test.user,
                            one_budget_for_all_traffic_sources=test.one_budget_for_all_traffic_sources,
                            traffic_group=test.traffic_group,
                            balance=test.balance,
                            one_budget_for_all_offers=test.one_budget_for_all_offers,
                            adding_date=test.adding_date,
                            lifetime=test.lifetime,
                            archived=test.archived)
            new_test.save()

            for ts in test_traffic_sources:
                new_test.traffic_sources.add(ts)

            for offer in test_offers:
                new_test.offers.add(offer)

            new_test.geo.add(geo)
            result.append(new_test)

        return result

    @staticmethod
    def split_by_traffic_sources(test):
        result = []

        test_offers = list(test.offers.all())
        test_traffic_sources = list(test.traffic_sources.all())
        test_geo = list(test.geo.all())

        for ts in test_traffic_sources:
            new_test = Test(budget=test.budget, user=test.user,
                            one_budget_for_all_geo=test.one_budget_for_all_geo,
                            traffic_group=test.traffic_group,
                            balance=test.balance,
                            one_budget_for_all_offers=test.one_budget_for_all_offers,
                            adding_date=test.adding_date,
                            lifetime=test.lifetime,
                            archived=test.archived)
            new_test.save()

            for geo in test_geo:
                new_test.geo.add(geo)

            for offer in test_offers:
                new_test.offers.add(offer)

            new_test.traffic_sources.add(ts)
            result.append(new_test)

        return result
