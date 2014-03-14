# Command mostly copied from django-storages fast collectstatic commadn
# https://bitbucket.org/maikhoepfel/django-storages/src/c99a01da29a959a3c919ab3e3debbf74abab5b85/storages/management/commands/collectstatic.py

from django.conf import settings
from django.contrib.staticfiles.management.commands import collectstatic
from django.core.management import call_command


class Command(collectstatic.Command):
    """
    This management command adds support to create GZIP versions of collected
    static files, by calling the `gzipstatic` command. It's custom behaviour
    is disabled by default; you explicitly need to set
    WHITENOISE_GZIP_COLLECTSTATIC to enable.
    """

    def collect(self):
        """
        Ensure that the storage class preloads the metadata. This is where the
        actual speedup comes from, as one request can pull the file hashes for
        many or all files in the bucket.
        """
        original_return = super(Command, self).collect()

        if getattr(settings, 'WHITENOISE_GZIP_COLLECTSTATIC', False):
            call_command('gzipstatic', verbosity=self.verbosity)

        return original_return
