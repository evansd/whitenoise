from __future__ import unicode_literals

import unittest

from whitenoise.string_utils import TEXT_TYPE

try:
    from urllib.parse import urljoin, urlparse
except ImportError:
    from urlparse import urljoin, urlparse
import shutil
import sys
import tempfile

import django
from django.test import SimpleTestCase
from django.test.utils import override_settings
from django.conf import settings
from django.contrib.staticfiles import storage, finders
from django.core.wsgi import get_wsgi_application
from django.core.management import call_command
from django.utils.functional import empty

import brotli

from whitenoise.middleware import WhiteNoiseMiddleware

from .utils import TestServer, Files

django.setup()


def reset_lazy_object(obj):
    obj._wrapped = empty


def get_url_path(base, url):
    return urlparse(urljoin(base, url)).path


@override_settings()
class DjangoWhiteNoiseTest(SimpleTestCase):

    @classmethod
    def setUpClass(cls):
        reset_lazy_object(storage.staticfiles_storage)
        cls.static_files = Files('static', js='app.js', nonascii='nonascii\u2713.txt')
        cls.root_files = Files('root', robots='robots.txt')
        cls.tmp = TEXT_TYPE(tempfile.mkdtemp())
        settings.STATICFILES_DIRS = [cls.static_files.directory]
        settings.STATIC_ROOT = cls.tmp
        settings.WHITENOISE_ROOT = cls.root_files.directory
        # Collect static files into STATIC_ROOT
        call_command('collectstatic', verbosity=0, interactive=False)
        # Initialize test application
        cls.application = get_wsgi_application()
        cls.server = TestServer(cls.application)
        super(DjangoWhiteNoiseTest, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        super(DjangoWhiteNoiseTest, cls).tearDownClass()
        reset_lazy_object(storage.staticfiles_storage)
        # Remove temporary directory
        shutil.rmtree(cls.tmp)

    def test_get_root_file(self):
        response = self.server.get(self.root_files.robots_url)
        self.assertEqual(response.content, self.root_files.robots_content)

    def test_versioned_file_cached_forever(self):
        url = storage.staticfiles_storage.url(self.static_files.js_path)
        response = self.server.get(url)
        self.assertEqual(response.content, self.static_files.js_content)
        self.assertEqual(response.headers.get('Cache-Control'),
                         'max-age={}, public, immutable'.format(WhiteNoiseMiddleware.FOREVER))

    def test_unversioned_file_not_cached_forever(self):
        url = settings.STATIC_URL + self.static_files.js_path
        response = self.server.get(url)
        self.assertEqual(response.content, self.static_files.js_content)
        self.assertEqual(response.headers.get('Cache-Control'),
                         'max-age={}, public'.format(WhiteNoiseMiddleware.max_age))

    def test_get_gzip(self):
        url = storage.staticfiles_storage.url(self.static_files.js_path)
        response = self.server.get(url)
        self.assertEqual(response.content, self.static_files.js_content)
        self.assertEqual(response.headers['Content-Encoding'], 'gzip')
        self.assertEqual(response.headers['Vary'], 'Accept-Encoding')

    def test_get_brotli(self):
        url = storage.staticfiles_storage.url(self.static_files.js_path)
        response = self.server.get(url, headers={'Accept-Encoding': 'gzip, br'})
        self.assertEqual(brotli.decompress(response.content), self.static_files.js_content)
        self.assertEqual(response.headers['Content-Encoding'], 'br')
        self.assertEqual(response.headers['Vary'], 'Accept-Encoding')

    def test_no_content_type_when_not_modified(self):
        last_mod = 'Fri, 11 Apr 2100 11:47:06 GMT'
        url = settings.STATIC_URL + self.static_files.js_path
        response = self.server.get(url, headers={'If-Modified-Since': last_mod})
        self.assertNotIn('Content-Type', response.headers)

    def test_get_nonascii_file(self):
        url = settings.STATIC_URL + self.static_files.nonascii_path
        response = self.server.get(url)
        self.assertEqual(response.content, self.static_files.nonascii_content)


@override_settings()
class PathlibTest(SimpleTestCase):

    @unittest.skipIf(sys.version_info < (3, 4), "Pathlib was added in Python 3.4")
    def test_pathlib_compat(self):
        from pathlib import Path
        settings.STATIC_ROOT = Path(tempfile.mkdtemp())
        app = get_wsgi_application()
        self.assertNotEqual(app, None)


@override_settings()
class UseFindersTest(SimpleTestCase):

    AUTOREFRESH = False

    @classmethod
    def setUpClass(cls):
        cls.static_files = Files(
                'static',
                js='app.js',
                index='with-index/index.html')
        settings.STATICFILES_DIRS = [cls.static_files.directory]
        settings.WHITENOISE_USE_FINDERS = True
        settings.WHITENOISE_AUTOREFRESH = cls.AUTOREFRESH
        settings.WHITENOISE_INDEX_FILE = True
        settings.STATIC_ROOT = None
        # Clear cache to pick up new settings
        try:
            finders.get_finder.cache_clear()
        except AttributeError:
            finders._finders.clear()
        # Initialize test application
        cls.application = get_wsgi_application()
        cls.server = TestServer(cls.application)
        super(UseFindersTest, cls).setUpClass()

    def test_file_served_from_static_dir(self):
        url = settings.STATIC_URL + self.static_files.js_path
        response = self.server.get(url)
        self.assertEqual(response.content, self.static_files.js_content)

    def test_non_ascii_requests_safely_ignored(self):
        response = self.server.get(settings.STATIC_URL + u"test\u263A")
        self.assertEqual(404, response.status_code)

    def test_requests_for_directory_safely_ignored(self):
        url = settings.STATIC_URL + 'directory'
        response = self.server.get(url)
        self.assertEqual(404, response.status_code)

    def test_index_file_served_at_directory_path(self):
        path = self.static_files.index_path.rpartition('/')[0] + '/'
        response = self.server.get(settings.STATIC_URL + path)
        self.assertEqual(response.content, self.static_files.index_content)

    def test_index_file_path_redirected(self):
        directory_path = self.static_files.index_path.rpartition('/')[0] + '/'
        index_url = settings.STATIC_URL + self.static_files.index_path
        response = self.server.get(index_url, allow_redirects=False)
        location = get_url_path(response.url, response.headers['Location'])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(location, settings.STATIC_URL + directory_path)

    def test_directory_path_without_trailing_slash_redirected(self):
        directory_path = self.static_files.index_path.rpartition('/')[0] + '/'
        directory_url = settings.STATIC_URL + directory_path.rstrip('/')
        response = self.server.get(directory_url, allow_redirects=False)
        location = get_url_path(response.url, response.headers['Location'])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(location, settings.STATIC_URL + directory_path)


class UseFindersAutorefreshTest(UseFindersTest):

    AUTOREFRESH = True
