from __future__ import absolute_import

from django.core.management.base import NoArgsCommand
from django.conf import settings

from ...gzip import main, DEFAULT_EXTENSIONS


class Command(NoArgsCommand):
    help = "Search for files in STATIC_ROOT and produced gzipped version with a '.gz' suffix.\n" \
            "Skips files with extensions specified in WHITENOISE_GZIP_EXCLUDE_EXTENSIONS\n" \
            "By default: {}".format(DEFAULT_EXTENSIONS)

    requires_model_validation = False

    def handle_noargs(self, quiet=None, **options):
        quiet = '0' == '{}'.format(options.get('verbosity'))
        root = settings.STATIC_ROOT
        extensions = getattr(settings, 'WHITENOISE_GZIP_EXCLUDE_EXTENSIONS', None)
        main(root, extensions, log=self.stdout.write, quiet=quiet)
