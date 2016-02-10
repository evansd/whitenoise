from __future__ import unicode_literals

import shutil
import tempfile

import django
from django.test import SimpleTestCase
from django.test.utils import override_settings
from django.conf import settings
from django.contrib.staticfiles import storage, finders
from django.core.wsgi import get_wsgi_application
from django.core.management import call_command
from django.utils.functional import empty

from .utils import TestServer, Files

from whitenoise.django import DjangoWhiteNoise

django.setup()


def reset_lazy_object(obj):
    obj._wrapped = empty


@override_settings()
class DjangoWhiteNoiseTest(SimpleTestCase):

    @classmethod
    def setUpClass(cls):
        cls.static_files = Files('static', css='styles.css')
        cls.root_files = Files('root', robots='robots.txt')
        cls.tmp = tempfile.mkdtemp()
        settings.STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
        settings.STATICFILES_DIRS = [cls.static_files.directory]
        settings.STATIC_ROOT = cls.tmp
        settings.WHITENOISE_ROOT = cls.root_files.directory
        # Collect static files into STATIC_ROOT
        call_command('collectstatic', verbosity=0, interactive=False)
        # Initialize test application
        cls.application = cls.init_application()
        cls.server = TestServer(cls.application)
        super(DjangoWhiteNoiseTest, cls).setUpClass()

    @classmethod
    def init_application(cls):
        django_app = get_wsgi_application()
        return DjangoWhiteNoise(django_app)

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
        url = storage.staticfiles_storage.url(self.static_files.css_path)
        response = self.server.get(url)
        self.assertEqual(response.content, self.static_files.css_content)
        self.assertEqual(response.headers.get('Cache-Control'),
                         'public, max-age={}'.format(DjangoWhiteNoise.FOREVER))

    def test_unversioned_file_not_cached_forever(self):
        url = settings.STATIC_URL + self.static_files.css_path
        response = self.server.get(url)
        self.assertEqual(response.content, self.static_files.css_content)
        self.assertEqual(response.headers.get('Cache-Control'),
                         'public, max-age={}'.format(DjangoWhiteNoise.max_age))

    def test_get_gzip(self):
        url = storage.staticfiles_storage.url(self.static_files.css_path)
        response = self.server.get(url)
        self.assertEqual(response.content, self.static_files.css_content)
        self.assertEqual(response.headers['Content-Encoding'], 'gzip')
        self.assertEqual(response.headers['Vary'], 'Accept-Encoding')


@override_settings()
class UseFindersTest(SimpleTestCase):

    @classmethod
    def setUpClass(cls):
        cls.static_files = Files('static', css='styles.css')
        settings.STATICFILES_DIRS = [cls.static_files.directory]
        settings.WHITENOISE_USE_FINDERS = True
        settings.WHITENOISE_AUTOREFRESH = True
        # Clear cache to pick up new settings
        try:
            finders.get_finder.cache_clear()
        except AttributeError:
            finders._finders.clear()
        # Initialize test application
        cls.application = cls.init_application()
        cls.server = TestServer(cls.application)
        super(UseFindersTest, cls).setUpClass()

    @classmethod
    def init_application(cls):
        django_app = get_wsgi_application()
        return DjangoWhiteNoise(django_app)

    def test_get_file_from_static_dir(self):
        url = settings.STATIC_URL + self.static_files.css_path
        response = self.server.get(url)
        self.assertEqual(response.content, self.static_files.css_content)


class DjangoMiddlewareTest(DjangoWhiteNoiseTest):

    @classmethod
    def init_application(cls):
        middleware = list(settings.MIDDLEWARE_CLASSES)
        middleware.insert(0, 'whitenoise.middleware.WhiteNoiseMiddleware')
        settings.MIDDLEWARE_CLASSES = middleware
        return get_wsgi_application()
