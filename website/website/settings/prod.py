# Copyright © 2020-2021 Filthy Claws Tools - All Rights Reserved
#
# This file is part of FCTools_payroll
#
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Author: German Yakimov <german13yakimov@gmail.com>

from website.settings.base import *

DEBUG = False

DATABASE_NAME = os.getenv("DATABASE_NAME")
DATABASE_HOST = os.getenv("DATABASE_HOST")
DATABASE_PORT = os.getenv("DATABASE_PORT")

ALLOWED_HOSTS = [
    "185.92.150.58",
    "team.fctools.ru",
    "127.0.0.1",
    "localhost",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": DATABASE_NAME,
        "USER": DATABASE_USER,
        "PASSWORD": DATABASE_PASSWORD,
        "HOST": DATABASE_HOST,
        "PORT": DATABASE_PORT,
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
    "handlers": {
        "file": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "filename": 'info_log.log',
            "formatter": "verbose"}},
    "root": {
        "handlers": ["file"],
        "level": "DEBUG", },
    "loggers": {
        "django": {
            "handlers": ["file"],
            "level": "DEBUG",
            "propagate": False, },
        "django.db_backends": {
            "handlers": ["file"],
            "level": "DEBUG",
            "propagate": False,
        },
        "django.db": {
            "handlers": ["file"],
            "level": "DEBUG",
            "propagate": False, },
    },
}

STATIC_ROOT = os.path.join(BASE_DIR, "static/")
