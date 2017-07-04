import django


ALLOWED_HOSTS = ['*']

ROOT_URLCONF = 'tests.django_urls'

SECRET_KEY = 'test_secret'

INSTALLED_APPS = [
    'whitenoise.runserver_nostatic',
    'django.contrib.staticfiles'
]

STATIC_URL = '/static/'

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
