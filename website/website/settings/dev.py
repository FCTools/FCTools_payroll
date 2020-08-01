"""
Copyright © 2020 FC Tools. All rights reserved.
Author: German Yakimov
"""

from .base import *

DEBUG = True

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": "fctools_info",
        "USER": DATABASE_USER,
        "PASSWORD": DATABASE_PASSWORD,
        "HOST": "localhost",
        "PORT": "",
    }
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
    },
    "handlers": {"console": {"class": "logging.StreamHandler", },
                 "file": {"level": "DEBUG", "class": "logging.FileHandler",
                          "filename": os.path.join('logs', 'debug_log.log'), "formatter": "verbose"}, },
    "root": {"handlers": ["console", "file"], "level": "INFO", },
    "loggers": {
        "django": {"handlers": ["console", "file"], "level": "INFO",
                   "propagate": False, },
        "django.db_backends": {
            "handlers": ["console", "file"],
            "level": "DEBUG",
            "propagate": False,
        },
        "django.db": {"handlers": ["console", "file"], "level": "DEBUG",
                      "propagate": False, },
    },
}

INSTALLED_APPS += ["debug_toolbar"]
MIDDLEWARE = ["debug_toolbar.middleware.DebugToolbarMiddleware"] + MIDDLEWARE

STATICFILES_DIRS = ["static", os.path.join(BASE_DIR, "static/")]
