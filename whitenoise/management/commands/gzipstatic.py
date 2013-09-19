from __future__ import absolute_import

from django.core.management.base import NoArgsCommand
from django.conf import settings

from ...gzip import main, DEFAULT_EXTENSIONS


class Command(NoArgsCommand):
    help = "Search for all files in STATIC_ROOT matching the extensions " \
            "specified in WHITENOISE_GZIP_EXTENSIONS (by default: {ext}) " \
            "and produce gzipped versions with a '.gz' suffix".format(
                    ext=', '.join(DEFAULT_EXTENSIONS))

    requires_model_validation = False

    def handle_noargs(self, quiet=None, **options):
        quiet = '0' == '{}'.format(options.get('verbosity'))
        root = settings.STATIC_ROOT
        extensions = getattr(settings, 'WHITENOISE_GZIP_EXTENSIONS', None)
        main(root, extensions, log=self.stdout.write, quiet=quiet)
