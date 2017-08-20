import django

from .utils import TestServer


ALLOWED_HOSTS = ['*']

ROOT_URLCONF = 'tests.django_urls'

SECRET_KEY = 'test_secret'

INSTALLED_APPS = [
    'whitenoise.runserver_nostatic',
    'django.contrib.staticfiles'
]

FORCE_SCRIPT_NAME = '/' + TestServer.PREFIX
STATIC_URL = FORCE_SCRIPT_NAME + '/static/'

# This path is not actually used, but we have to set it to something
# or Django will complain
STATIC_ROOT = '/dev/null'

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

if django.VERSION >= (1, 10):
    MIDDLEWARE = ['whitenoise.middleware.WhiteNoiseMiddleware']
else:
    MIDDLEWARE_CLASSES = ['whitenoise.middleware.WhiteNoiseMiddleware']


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'log_to_stderr': {
            'level': 'ERROR',
            'class': 'logging.StreamHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['log_to_stderr'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}
