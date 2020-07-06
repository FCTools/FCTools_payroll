# from .base import *
from website.website.settings.base import *


DEBUG = False

ALLOWED_HOSTS = [
    '185.92.150.58',
    'team.fctools.ru',
    '127.0.0.1',
    'localhost',
]

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

STATIC_URL = os.path.join(BASE_DIR, 'static/')
# STATIC_URL = '/static/'
# STATIC_ROOT = os.path.join(BASE_DIR, 'static/')
STATIC_ROOT = 'static/'
MEDIA_URL = os.path.join(BASE_DIR, 'media/')
MEDIA_ROOT = os.path.join(BASE_DIR, 'media/')
