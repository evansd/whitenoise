from __future__ import absolute_import, unicode_literals

import errno
import os
import shutil
import tempfile
from unittest import TestCase
from wsgiref.simple_server import demo_app

from .utils import TestServer, gzip_bytes
from whitenoise import WhiteNoise

TEST_FILES = {
    '/some/test.js': b'this is some javascript',
    '/compress.css': b'some css goes here'
}
TEST_FILES['/compress.css.gz'] = gzip_bytes(TEST_FILES['/compress.css'])

class WhiteNoiseTest(TestCase):

    @classmethod
    def setUpClass(cls):
        # Make a temporary directory
        cls.tmp = tempfile.mkdtemp()
        for path, contents in TEST_FILES.items():
            path = os.path.join(cls.tmp, path.lstrip('/'))
            try:
                os.makedirs(os.path.dirname(path))
            except OSError as e:
                if e.errno != errno.EEXIST:
                    raise
            with open(path, 'wb') as f:
                f.write(contents)
        cls.application = WhiteNoise(demo_app,
                root=cls.tmp, default_max_age = 1000)
        cls.server = TestServer(cls.application)
        super(WhiteNoiseTest, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        super(WhiteNoiseTest, cls).tearDownClass()
        # Remove temporary directory
        shutil.rmtree(cls.tmp)

    def tmp_dir(self):
        return tempfile.mkdtemp(dir=self.tmp)

    def test_get_file(self):
        response = self.server.get('/some/test.js')
        self.assertEqual(response.content, TEST_FILES['/some/test.js'])
        self.assertEqual(response.headers['Content-Type'], 'application/javascript')

    def test_get_non_gzip(self):
        response = self.server.get('/compress.css', headers={'Accept-Encoding': ''})
        self.assertEqual(response.content, TEST_FILES['/compress.css'])
        self.assertEqual(response.headers.get('Content-Encoding', ''), '')
        self.assertEqual(response.headers['Vary'], 'Accept-Encoding')

    def test_get_gzip(self):
        response = self.server.get('/compress.css')
        self.assertEqual(response.content, TEST_FILES['/compress.css'])
        self.assertEqual(response.headers['Content-Encoding'], 'gzip')
        self.assertEqual(response.headers['Vary'], 'Accept-Encoding')

    def test_not_modified(self):
        response = self.server.get('/some/test.js')
        last_mod = response.headers['Last-Modified']
        response = self.server.get('/some/test.js', headers={'If-Modified-Since': last_mod})
        self.assertEqual(response.status_code, 304)

    def test_max_age(self):
        response = self.server.get('/some/test.js')
        self.assertEqual(response.headers['Cache-Control'], 'public, max-age=1000')

    def test_other_requests_passed_through(self):
        response = self.server.get('/not/static')
        self.assertIn('Hello world!', response.text)

    def test_add_under_prefix(self):
        self.application.add_files(self.tmp, prefix='prefix/')
        response = self.server.get('/prefix/some/test.js')
        self.assertEqual(response.content, TEST_FILES['/some/test.js'])
