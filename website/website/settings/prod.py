from website.settings.base import *


DEBUG = False
SECRET_KEY = os.getenv("SECRET_KEY")

ALLOWED_HOSTS = [
    "185.92.150.58",
    "team.fctools.ru",
    "127.0.0.1",
    "localhost",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": os.getenv("DATABASE_NAME"),
        "USER": os.getenv("DATABASE_USER"),
        "PASSWORD": os.getenv("DATABASE_PASSWORD"),
        "HOST": os.getenv("DATABASE_HOST"),
        "PORT": os.getenv("DATABASE_PORT"),
    }
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler", }, },
    "root": {"handlers": ["console"], "level": "WARNING", },
    "loggers": {"django": {"handlers": ["console"], "level": "INFO", "propagate": False, }, },
}

STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "static/")

MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media/")
