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
    "handlers": {"console": {"class": "logging.StreamHandler",},},
    "root": {"handlers": ["console"], "level": "DEBUG",},
    "loggers": {
        "django": {"handlers": ["console"], "level": os.getenv("DJANGO_LOG_LEVEL", "INFO"), "propagate": False,},
        "django.db_backends": {
            "handlers": ["console"],
            "level": os.getenv("DJANGO_LOG_LEVEL", "DEBUG"),
            "propagate": False,
        },
        "django.db": {"handlers": ["console"], "level": os.getenv("DJANGO_LOG_LEVEL", "DEBUG"), "propagate": False,},
    },
}

INSTALLED_APPS += ["debug_toolbar"]
MIDDLEWARE = ["debug_toolbar.middleware.DebugToolbarMiddleware"] + MIDDLEWARE

STATIC_URL = "/static/"
MEDIA_URL = "/media/"

STATICFILES_DIRS = ["static", os.path.join(BASE_DIR, "static/")]
