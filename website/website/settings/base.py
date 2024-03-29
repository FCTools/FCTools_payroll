# Copyright © 2020-2021 Filthy Claws Tools - All Rights Reserved
#
# This file is part of FCTools_payroll
#
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Author: German Yakimov <german13yakimov@gmail.com>

import os

from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import TableStyle

SECRET_KEY = os.getenv("SECRET_KEY")

BASE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..")

ALLOWED_HOSTS = []

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "crispy_forms",
    "tempus_dominus",

    "fctools_salary",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",

    "fctools_salary.middleware.UpdateDatabaseMiddleware",
]

ROOT_URLCONF = "website.urls"

LOGIN_REDIRECT_URL = "/"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "website.wsgi.application"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator", },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator", },
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator", },
]

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

USE_TZ = True

INTERNAL_IPS = [
    "127.0.0.1",
    "localhost",
]

TRAFFIC_GROUPS = (
    ("ADMIN", "ADMIN"),
    ("FPA/HSA/PWA", "FPA/HSA/PWA"),
    ("INAPP traff", "INAPP traff"),
    ("NATIVE traff", "NATIVE traff"),
    ("POP traff", "POP traff"),
    ("PUSH traff", "PUSH traff"),
    ("Tik Tok", "Tik Tok")
)

# traffic groups
ADMIN = "ADMIN"
FPA_HSA_PWA = "FPA/HSA/PWA"
INAPP_TRAFF = "INAPP traff"
NATIVE_TRAFF = "NATIVE traff"
POP_TRAFF = "POP traff"
PUSH_TRAFF = "PUSH traff"
TIK_TOK = "Tik Tok"

TRAFFIC_GROUPS = (
    (ADMIN, ADMIN),
    (FPA_HSA_PWA, FPA_HSA_PWA),
    (INAPP_TRAFF, INAPP_TRAFF),
    (NATIVE_TRAFF, NATIVE_TRAFF),
    (POP_TRAFF, POP_TRAFF),
    (PUSH_TRAFF, PUSH_TRAFF),
    (TIK_TOK, TIK_TOK)
)

REDIS_HOST = 'localhost'
REDIS_PORT = '6214'

# settings for pdf reports generating
TABLE_STYLE = TableStyle([("GRID", (0, 0), (-1, -1), 2, colors.black), ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                          ("FONTSIZE", (0, 0), (-1, -1), 12), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                          ("LEADING", (0, 0), (-1, -1), 15)])

PARAGRAPH_STYLE_FONT_11 = ParagraphStyle(name="style", alignment=1, fontSize=11, leading=15)
PARAGRAPH_STYLE_FONT_12 = ParagraphStyle(name="style", alignment=1, fontSize=12, leading=15)

BINOM_API_KEY = os.getenv("BINOM_API_KEY")
TRACKER_URL = "https://fcttrk.com/"

DATABASE_USER = os.getenv("DATABASE_USER")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")

MEDIA_ROOT = os.path.join(BASE_DIR, "media/")
MEDIA_URL = "/media/"

STATIC_URL = "/static/"
