import django


ALLOWED_HOSTS = ['*']

ROOT_URLCONF = 'tests.django_urls'

SECRET_KEY = 'test_secret'

INSTALLED_APPS = [
    'django.contrib.staticfiles'
]

STATIC_URL = '/static/'

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

if django.VERSION >= (1, 10):
    MIDDLEWARE = ['whitenoise.django.WhiteNoiseMiddleware']
else:
    MIDDLEWARE_CLASSES = ['whitenoise.django.WhiteNoiseMiddleware']
