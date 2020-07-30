
class UpdateError(Exception):
    """
    This error raises when we can't get some info from tracker for any reason,
    e.g. network error or incorrect response from tracker.
    """

    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


class TestNotSplitError(Exception):
    """
    This error raises when some test doesn't split by traffic sources or by geo.
    """

    def __init__(self, test_id):
        self.message = f"Test {test_id} has more than 1 traffic sources (or geo), " \
                       f"but one_budget_for_all_traffic_sources (one_budget_for_all_geo) set to False. " \
                       f"Please, set flag to True or split this test by traffic sources (or/and by geo)."

    def __str__(self):
        return self.message
