
class UpdateError(Exception):
    """
    This error raises when we can't get some info from tracker for any reason,
    e.g. network error or incorrect response from tracker.
    """

    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message
