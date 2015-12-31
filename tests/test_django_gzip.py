from __future__ import unicode_literals

from django.test import SimpleTestCase
from django.test.utils import override_settings
from django.conf import settings
from django.core.management import call_command

from .test_gzip import GzipTest


@override_settings()
class DjangoGzipTest(GzipTest, SimpleTestCase):

    @classmethod
    def run_gzip(cls):
        settings.STATIC_ROOT = cls.tmp
        call_command('gzipstatic', verbosity=0)
