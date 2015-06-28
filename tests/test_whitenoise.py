from __future__ import absolute_import

import errno
import os
import shutil
import sys
import tempfile
if sys.version_info[:2] <= (2, 6):
    from unittest2 import TestCase
else:
    from unittest import TestCase
from wsgiref.simple_server import demo_app

from .utils import TestServer, gzip_bytes

from whitenoise import WhiteNoise


# Update Py2 TestCase to support Py3 method names
if not hasattr(TestCase, 'assertRegex'):
    class Py3TestCase(TestCase):
        def assertRegex(self, *args, **kwargs):
            return self.assertRegexpMatches(*args, **kwargs)
    TestCase = Py3TestCase


# Define files we're going to test against
JS_FILE = '/some/test.js'
GZIP_FILE = '/compress.css'
CUSTOM_MIME_FILE = '/myfile.foobar'
TEST_FILES = {
    JS_FILE: b'this is some javascript',
    GZIP_FILE: b'some css goes here',
    CUSTOM_MIME_FILE: b'stuff here'
}
# Gzipped version of GZIPFILE
TEST_FILES[GZIP_FILE + '.gz'] = gzip_bytes(TEST_FILES[GZIP_FILE])


class CustomWhiteNoise(WhiteNoise):

    EXTRA_MIMETYPES = WhiteNoise.EXTRA_MIMETYPES + (
            ('application/x-foo-bar', '.foobar'),)


class WhiteNoiseTest(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        cls.createTestFiles()
        # Initialize test application
        cls.application = CustomWhiteNoise(demo_app,
                root=cls.tmp, max_age=1000)
        cls.server = TestServer(cls.application)
        super(WhiteNoiseTest, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        super(WhiteNoiseTest, cls).tearDownClass()
        # Remove temporary directory
        shutil.rmtree(cls.tmp)

    @classmethod
    def createTestFiles(cls):
        # Make a temporary directory and copy in test files
        for path, contents in TEST_FILES.items():
            path = os.path.join(cls.tmp, path.lstrip('/'))
            try:
                os.makedirs(os.path.dirname(path))
            except OSError as e:
                if e.errno != errno.EEXIST:
                    raise
            with open(path, 'wb') as f:
                f.write(contents)

    def test_get_file(self):
        response = self.server.get(JS_FILE)
        self.assertEqual(response.content, TEST_FILES[JS_FILE])
        self.assertRegex(response.headers['Content-Type'], r'application/javascript\b')
        self.assertRegex(response.headers['Content-Type'], r'.*\bcharset="utf-8"')

    def test_get_not_accept_gzip(self):
        response = self.server.get(GZIP_FILE, headers={'Accept-Encoding': ''})
        self.assertEqual(response.content, TEST_FILES[GZIP_FILE])
        self.assertEqual(response.headers.get('Content-Encoding', ''), '')
        self.assertEqual(response.headers['Vary'], 'Accept-Encoding')

    def test_get_accept_gzip(self):
        response = self.server.get(GZIP_FILE)
        self.assertEqual(response.content, TEST_FILES[GZIP_FILE])
        self.assertEqual(response.headers['Content-Encoding'], 'gzip')
        self.assertEqual(response.headers['Vary'], 'Accept-Encoding')

    def test_not_modified_exact(self):
        response = self.server.get(JS_FILE)
        last_mod = response.headers['Last-Modified']
        response = self.server.get(JS_FILE, headers={'If-Modified-Since': last_mod})
        self.assertEqual(response.status_code, 304)

    def test_not_modified_future(self):
        response = self.server.get(JS_FILE)
        last_mod = 'Fri, 11 Apr 2100 11:47:06 GMT'
        response = self.server.get(JS_FILE, headers={'If-Modified-Since': last_mod})
        self.assertEqual(response.status_code, 304)

    def test_modified(self):
        response = self.server.get(JS_FILE)
        last_mod = 'Fri, 11 Apr 2001 11:47:06 GMT'
        response = self.server.get(JS_FILE, headers={'If-Modified-Since': last_mod})
        self.assertEqual(response.status_code, 200)

    def test_max_age(self):
        response = self.server.get(JS_FILE)
        self.assertEqual(response.headers['Cache-Control'], 'public, max-age=1000')

    def test_other_requests_passed_through(self):
        response = self.server.get('/not/static')
        self.assertIn('Hello world!', response.text)

    def test_add_under_prefix(self):
        prefix = '/prefix'
        self.application.add_files(self.tmp, prefix=prefix)
        response = self.server.get(prefix + JS_FILE)
        self.assertEqual(response.content, TEST_FILES[JS_FILE])

    def test_response_has_allow_origin_header(self):
        for name in TEST_FILES:
            response = self.server.get(name)
            self.assertEqual(response.headers.get('Access-Control-Allow-Origin'), '*')

    def test_response_has_correct_content_length_header(self):
        response = self.server.get(JS_FILE)
        length = int(response.headers['Content-Length'])
        self.assertEqual(length, len(TEST_FILES[JS_FILE]))

    def test_gzip_response_has_correct_content_length_header(self):
        response = self.server.get(GZIP_FILE)
        length = int(response.headers['Content-Length'])
        self.assertEqual(length, len(TEST_FILES[GZIP_FILE + '.gz']))

    def test_post_request_returns_405(self):
        response = self.server.request('post', JS_FILE)
        self.assertEqual(response.status_code, 405)

    def test_head_request_has_no_body(self):
        response = self.server.request('head', JS_FILE)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.content)

    def test_custom_mimetpye(self):
        response = self.server.get(CUSTOM_MIME_FILE)
        self.assertRegex(response.headers['Content-Type'], r'application/x-foo-bar\b')


class WhiteNoiseAutorefreshTest(WhiteNoiseTest):

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        # Initialize test application
        cls.application = CustomWhiteNoise(demo_app,
                root=cls.tmp, max_age=1000, autorefresh=True)
        cls.server = TestServer(cls.application)
        # This time we create files *after* initializing server
        cls.createTestFiles()
        super(WhiteNoiseTest, cls).setUpClass()
