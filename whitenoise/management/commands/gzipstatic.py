from __future__ import absolute_import

import django
from django.core.management.base import NoArgsCommand
from django.conf import settings

from ...gzip import main, GZIP_EXCLUDE_EXTENSIONS


class Command(NoArgsCommand):
    help = "Search for files in STATIC_ROOT and produced gzipped version with a '.gz' suffix.\n" \
            "Skips files with extensions specified in WHITENOISE_GZIP_EXCLUDE_EXTENSIONS\n" \
            "By default: {}".format(GZIP_EXCLUDE_EXTENSIONS)

    if django.VERSION < (1, 7):
        requires_model_validation = False
    else:
        requires_system_checks = False

    def handle_noargs(self, quiet=None, **options):
        quiet = '0' == str(options.get('verbosity'))
        root = settings.STATIC_ROOT
        extensions = getattr(settings, 'WHITENOISE_GZIP_EXCLUDE_EXTENSIONS',
                GZIP_EXCLUDE_EXTENSIONS)
        main(root, extensions, log=self.stdout.write, quiet=quiet)
