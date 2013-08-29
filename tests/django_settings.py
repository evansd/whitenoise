SECRET_KEY = '4'
STATIC_URL = '/static/'

ROOT_URLCONF = 'tests.django_urls'

INSTALLED_APPS = (
    'django.contrib.staticfiles',
    'whitenoise',
)

ALLOWED_HOSTS = ['*']

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
