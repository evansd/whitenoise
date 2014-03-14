from __future__ import absolute_import, unicode_literals

from django.test import SimpleTestCase
from django.test.utils import override_settings
from django.conf import settings
from django.core.management import call_command

from .test_gzip import GzipTest


@override_settings()
class DjangoCollectStaticGzipTest(GzipTest, SimpleTestCase):

    @classmethod
    def run_gzip(cls):
        settings.STATIC_ROOT = cls.tmp
        settings.WHITENOISE_GZIP_COLLECTSTATIC = True
        call_command('collectstatic', interactive=False, verbosity=0)
