from __future__ import absolute_import, unicode_literals

import errno
import os
import shutil
import tempfile

import django
from django.test import SimpleTestCase
from django.test.utils import override_settings
from django.conf import settings
from django.contrib.staticfiles import storage
try:
    from django.contrib.staticfiles.storage import HashedFilesMixin
except ImportError:
    from django.contrib.staticfiles.storage import (
            CachedFilesMixin as HashedFilesMixin)
from django.core.wsgi import get_wsgi_application
from django.core.management import call_command

from .utils import TestServer

from whitenoise.django import (DjangoWhiteNoise, GzipStaticFilesMixin,
        MissingFileError)

# For Django 1.7+ ensure app registry is ready
if hasattr(django, 'setup'):
    django.setup()

ROOT_FILE = '/robots.txt'
ASSET_FILE = '/some/test.some.file.js'
TEST_FILES = {
    'root' + ROOT_FILE: b'some text',
    'static' + ASSET_FILE: b'this is some javascript' * 10
}


@override_settings()
class DjangoWhiteNoiseTest(SimpleTestCase):

    @classmethod
    def setUpClass(cls):
        # Keep a record of the original lazy storage instance so we can
        # restore it afterwards. We overwrite this in the setUp method so
        # that any new settings get picked up.
        if not hasattr(cls, '_originals'):
            cls._originals = {'staticfiles_storage': storage.staticfiles_storage}
        # Make a temporary directory and copy in test files
        cls.tmp = tempfile.mkdtemp()
        settings.STATICFILES_STORAGE = 'whitenoise.django.GzipManifestStaticFilesStorage'
        settings.STATICFILES_DIRS = [os.path.join(cls.tmp, 'static')]
        settings.STATIC_ROOT = os.path.join(cls.tmp, 'static_root')
        settings.WHITENOISE_ROOT = os.path.join(cls.tmp, 'root')
        for path, contents in TEST_FILES.items():
            path = os.path.join(cls.tmp, path.lstrip('/'))
            try:
                os.makedirs(os.path.dirname(path))
            except OSError as e:
                if e.errno != errno.EEXIST:
                    raise
            with open(path, 'wb') as f:
                f.write(contents)
        # Collect static files into STATIC_ROOT
        call_command('collectstatic', verbosity=0, interactive=False)
        # Initialize test application
        django_app = get_wsgi_application()
        cls.application = DjangoWhiteNoise(django_app)
        cls.server = TestServer(cls.application)
        super(DjangoWhiteNoiseTest, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        super(DjangoWhiteNoiseTest, cls).tearDownClass()
        # Restore monkey-patched values
        if hasattr(cls, '_originals'):
            storage.staticfiles_storage = cls._originals['staticfiles_storage']
            del cls._originals
        # Remove temporary directory
        shutil.rmtree(cls.tmp)

    def setUp(self):
        # Configure a new lazy storage instance so it will pick up
        # any new settings
        storage.staticfiles_storage = storage.ConfiguredStorage()

    def test_get_root_file(self):
        url = ROOT_FILE
        response = self.server.get(url)
        self.assertEqual(response.content, TEST_FILES['root' + ROOT_FILE])

    def test_versioned_file_cached_forever(self):
        url = storage.staticfiles_storage.url(ASSET_FILE.lstrip('/'))
        response = self.server.get(url)
        self.assertEqual(response.content, TEST_FILES['static' + ASSET_FILE])
        self.assertEqual(response.headers.get('Cache-Control'),
                'public, max-age={}'.format(DjangoWhiteNoise.FOREVER))

    def test_unversioned_file_not_cached_forever(self):
        url = settings.STATIC_URL + ASSET_FILE.lstrip('/')
        response = self.server.get(url)
        self.assertEqual(response.content, TEST_FILES['static' + ASSET_FILE])
        self.assertEqual(response.headers.get('Cache-Control'),
                'public, max-age={}'.format(DjangoWhiteNoise.max_age))

    def test_get_gzip(self):
        url = storage.staticfiles_storage.url(ASSET_FILE.lstrip('/'))
        response = self.server.get(url)
        self.assertEqual(response.content, TEST_FILES['static' + ASSET_FILE])
        self.assertEqual(response.headers['Content-Encoding'], 'gzip')
        self.assertEqual(response.headers['Vary'], 'Accept-Encoding')


@override_settings()
class DjangoWhiteNoiseStorageTest(SimpleTestCase):

    def test_make_helpful_exception(self):
        class TriggerException(HashedFilesMixin):
            def exists(self, path):
                return False
        exception = None
        try:
            TriggerException().hashed_name('/missing/file.png')
        except ValueError as e:
            exception = e
        helpful_exception = GzipStaticFilesMixin() \
                .make_helpful_exception(exception, 'styles/app.css')
        self.assertIsInstance(helpful_exception, MissingFileError)
