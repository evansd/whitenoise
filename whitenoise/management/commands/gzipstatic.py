from __future__ import absolute_import

from optparse import make_option

from django.core.management.base import NoArgsCommand
from django.conf import settings

from ...gzip import main, DEFAULT_EXTENSIONS


class Command(NoArgsCommand):
    help = "Search for all files in STATIC_ROOT matching the extensions " \
            "specified in WHITENOISE_GZIP_EXTENSIONS (by default: {ext}) " \
            "and produce gzipped versions with a '.gz' suffix".format(
                    ext=', '.join(DEFAULT_EXTENSIONS))

    option_list = NoArgsCommand.option_list + (
        make_option('--quiet',
            action='store_true',
            dest='quiet',
            default=False,
            help="Don't produce any log ouput"),
        make_option('--force',
            action='store_true',
            dest='force',
            default=False,
            help="Overwrite pre-existing .gz files"),
        )

    requires_model_validation = False

    def handle_noargs(self, force=None, quiet=None, **options):
        root = settings.STATIC_ROOT
        extensions = getattr(settings, 'WHITENOISE_GZIP_EXTENSIONS', None)
        main(root, extensions, log=self.stdout.write, force=force, quiet=quiet)
