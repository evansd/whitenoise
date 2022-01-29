import os.path

from .utils import AppServer, TEST_FILE_PATH


ALLOWED_HOSTS = ["*"]

ROOT_URLCONF = "tests.django_urls"

SECRET_KEY = "test_secret"

INSTALLED_APPS = ["whitenoise.runserver_nostatic", "django.contrib.staticfiles"]

FORCE_SCRIPT_NAME = "/" + AppServer.PREFIX
STATIC_URL = FORCE_SCRIPT_NAME + "/static/"

STATIC_ROOT = os.path.join(TEST_FILE_PATH, "root")

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MIDDLEWARE = ["whitenoise.middleware.WhiteNoiseMiddleware"]

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {"require_debug_false": {"()": "django.utils.log.RequireDebugFalse"}},
    "handlers": {"log_to_stderr": {"level": "ERROR", "class": "logging.StreamHandler"}},
    "loggers": {
        "django.request": {
            "handlers": ["log_to_stderr"],
            "level": "ERROR",
            "propagate": True,
        }
    },
}
