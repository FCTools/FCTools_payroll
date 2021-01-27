"""
Copyright © 2020-2021 FC Tools.
All rights reserved.
Author: German Yakimov
"""

import functools

import requests


def catch_network_errors(method):
    """
    Decorator for requests errors catching.

    :param method: method to decorate
    :return: wrapper
    """

    @functools.wraps(method)
    def wrapper(*args, **kwargs):
        try:
            return method(*args, **kwargs)
        except (
                requests.exceptions.HTTPError,
                requests.exceptions.ConnectTimeout,
                requests.exceptions.Timeout,
                requests.exceptions.ConnectionError,
                requests.exceptions.RequestException,
                Exception,
        ) as network_error:
            return network_error

    return wrapper


@catch_network_errors
def get(session, *args, **kwargs):
    """
    Make GET-request using given session with errors catching.

    :param session: session to make request
    :param args: args
    :param kwargs: kwargs
    :return: response if success, else exception
    """

    return session.get(*args, **kwargs)


@catch_network_errors
def post(session, *args, **kwargs):
    """
    Make POST-request using given session.

    :param session: session to make request
    :param args: args
    :param kwargs: kwargs
    :return: response if success, else exception
    """

    return session.post(*args, **kwargs)
