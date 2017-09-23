import os
import tempfile
from unittest import TestCase
try:
    from urllib.parse import urljoin
except ImportError:
    from urlparse import urljoin
import shutil
from wsgiref.simple_server import demo_app

from .utils import TestServer, Files

from whitenoise import WhiteNoise


# Update Py2 TestCase to support Py3 method names
if not hasattr(TestCase, 'assertRegex'):
    class Py3TestCase(TestCase):
        def assertRegex(self, *args, **kwargs):
            return self.assertRegexpMatches(*args, **kwargs)
    TestCase = Py3TestCase


class WhiteNoiseTest(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.files = cls.init_files()
        cls.application = cls.init_application(root=cls.files.directory)
        cls.server = TestServer(cls.application)
        super(WhiteNoiseTest, cls).setUpClass()

    @staticmethod
    def init_files():
        return Files('assets',
                     js='subdir/javascript.js',
                     gzip='compressed.css',
                     gzipped='compressed.css.gz',
                     custom_mime='custom-mime.foobar',
                     index='with-index/index.html')

    @staticmethod
    def init_application(**kwargs):
        def custom_headers(headers, path, url):
            if url.endswith('.css'):
                headers['X-Is-Css-File'] = 'True'
        kwargs.update(max_age=1000,
                      mimetypes={'.foobar': 'application/x-foo-bar'},
                      add_headers_function=custom_headers,
                      index_file=True)
        return WhiteNoise(demo_app, **kwargs)

    def test_get_file(self):
        response = self.server.get(self.files.js_url)
        self.assertEqual(response.content, self.files.js_content)
        self.assertRegex(response.headers['Content-Type'], r'application/javascript\b')
        self.assertRegex(response.headers['Content-Type'], r'.*\bcharset="utf-8"')

    def test_get_not_accept_gzip(self):
        response = self.server.get(self.files.gzip_url, headers={'Accept-Encoding': ''})
        self.assertEqual(response.content, self.files.gzip_content)
        self.assertEqual(response.headers.get('Content-Encoding', ''), '')
        self.assertEqual(response.headers['Vary'], 'Accept-Encoding')

    def test_get_accept_gzip(self):
        response = self.server.get(self.files.gzip_url)
        self.assertEqual(response.content, self.files.gzip_content)
        self.assertEqual(response.headers['Content-Encoding'], 'gzip')
        self.assertEqual(response.headers['Vary'], 'Accept-Encoding')

    def test_cannot_directly_request_gzipped_file(self):
        response = self.server.get(self.files.gzip_url + '.gz')
        self.assert_is_default_response(response)

    def test_not_modified_exact(self):
        response = self.server.get(self.files.js_url)
        last_mod = response.headers['Last-Modified']
        response = self.server.get(self.files.js_url, headers={'If-Modified-Since': last_mod})
        self.assertEqual(response.status_code, 304)

    def test_not_modified_future(self):
        last_mod = 'Fri, 11 Apr 2100 11:47:06 GMT'
        response = self.server.get(self.files.js_url, headers={'If-Modified-Since': last_mod})
        self.assertEqual(response.status_code, 304)

    def test_modified(self):
        last_mod = 'Fri, 11 Apr 2001 11:47:06 GMT'
        response = self.server.get(self.files.js_url, headers={'If-Modified-Since': last_mod})
        self.assertEqual(response.status_code, 200)

    def test_etag_matches(self):
        response = self.server.get(self.files.js_url)
        etag = response.headers['ETag']
        response = self.server.get(self.files.js_url, headers={'If-None-Match': etag})
        self.assertEqual(response.status_code, 304)

    def test_etag_doesnt_match(self):
        etag = '"594bd1d1-36"'
        response = self.server.get(self.files.js_url, headers={'If-None-Match': etag})
        self.assertEqual(response.status_code, 200)

    def test_max_age(self):
        response = self.server.get(self.files.js_url)
        self.assertEqual(response.headers['Cache-Control'], 'max-age=1000, public')

    def test_other_requests_passed_through(self):
        response = self.server.get('/%s/not/static' % TestServer.PREFIX)
        self.assert_is_default_response(response)

    def test_non_ascii_requests_safely_ignored(self):
        response = self.server.get(u'/{}/test\u263A'.format(TestServer.PREFIX))
        self.assert_is_default_response(response)

    def test_add_under_prefix(self):
        prefix = '/prefix'
        self.application.add_files(self.files.directory, prefix=prefix)
        response = self.server.get('/{}{}/{}'.format(TestServer.PREFIX, prefix, self.files.js_path))
        self.assertEqual(response.content, self.files.js_content)

    def test_response_has_allow_origin_header(self):
        response = self.server.get(self.files.js_url)
        self.assertEqual(response.headers.get('Access-Control-Allow-Origin'), '*')

    def test_response_has_correct_content_length_header(self):
        response = self.server.get(self.files.js_url)
        length = int(response.headers['Content-Length'])
        self.assertEqual(length, len(self.files.js_content))

    def test_gzip_response_has_correct_content_length_header(self):
        response = self.server.get(self.files.gzip_url)
        length = int(response.headers['Content-Length'])
        self.assertEqual(length, len(self.files.gzipped_content))

    def test_post_request_returns_405(self):
        response = self.server.request('post', self.files.js_url)
        self.assertEqual(response.status_code, 405)

    def test_head_request_has_no_body(self):
        response = self.server.request('head', self.files.js_url)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.content)

    def test_custom_mimetype(self):
        response = self.server.get(self.files.custom_mime_url)
        self.assertRegex(response.headers['Content-Type'], r'application/x-foo-bar\b')

    def test_custom_headers(self):
        response = self.server.get(self.files.gzip_url)
        self.assertEqual(response.headers['x-is-css-file'], 'True')

    def test_index_file_served_at_directory_path(self):
        directory_url = self.files.index_url.rpartition('/')[0] + '/'
        response = self.server.get(directory_url)
        self.assertEqual(response.content, self.files.index_content)

    def test_index_file_path_redirected(self):
        directory_url = self.files.index_url.rpartition('/')[0] + '/'
        response = self.server.get(self.files.index_url, allow_redirects=False)
        location = urljoin(self.files.index_url, response.headers['Location'])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(location, directory_url)

    def test_directory_path_without_trailing_slash_redirected(self):
        directory_url = self.files.index_url.rpartition('/')[0] + '/'
        no_slash_url = directory_url.rstrip('/')
        response = self.server.get(no_slash_url, allow_redirects=False)
        location = urljoin(no_slash_url, response.headers['Location'])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(location, directory_url)

    def test_request_initial_bytes(self):
        response = self.server.get(
                self.files.js_url, headers={'Range': 'bytes=0-13'})
        self.assertEqual(response.content, self.files.js_content[0:14])

    def test_request_trailing_bytes(self):
        response = self.server.get(
                self.files.js_url, headers={'Range': 'bytes=-3'})
        self.assertEqual(response.content, self.files.js_content[-3:])

    def test_request_middle_bytes(self):
        response = self.server.get(
                self.files.js_url, headers={'Range': 'bytes=21-30'})
        self.assertEqual(response.content, self.files.js_content[21:31])

    def test_overlong_ranges_truncated(self):
        response = self.server.get(
                self.files.js_url, headers={'Range': 'bytes=21-100000'})
        self.assertEqual(response.content, self.files.js_content[21:])

    def test_overlong_trailing_ranges_return_entire_file(self):
        response = self.server.get(
                self.files.js_url, headers={'Range': 'bytes=-100000'})
        self.assertEqual(response.content, self.files.js_content)

    def test_out_of_range_error(self):
        response = self.server.get(
                self.files.js_url, headers={'Range': 'bytes=10000-11000'})
        self.assertEqual(response.status_code, 416)
        self.assertEqual(
                response.headers['Content-Range'],
                'bytes */%s' % len(self.files.js_content))

    def assert_is_default_response(self, response):
        self.assertIn('Hello world!', response.text)


class WhiteNoiseAutorefresh(WhiteNoiseTest):

    @classmethod
    def setUpClass(cls):
        cls.files = cls.init_files()
        cls.tmp = tempfile.mkdtemp()
        cls.application = cls.init_application(root=cls.tmp, autorefresh=True)
        cls.server = TestServer(cls.application)
        # Copy in the files *after* initializing server
        copytree(cls.files.directory, cls.tmp)
        super(WhiteNoiseTest, cls).setUpClass()

    def test_no_error_on_very_long_filename(self):
        response = self.server.get('/blah' * 1000)
        self.assertNotEqual(response.status_code, 500)

    @classmethod
    def tearDownClass(cls):
        super(WhiteNoiseTest, cls).tearDownClass()
        # Remove temporary directory
        shutil.rmtree(cls.tmp)


def copytree(src, dst):
    for name in os.listdir(src):
        src_path = os.path.join(src, name)
        dst_path = os.path.join(dst, name)
        if os.path.isdir(src_path):
            shutil.copytree(src_path, dst_path)
        else:
            shutil.copy2(src_path, dst_path)


class WhiteNoiseUnitTests(TestCase):

    def test_immutable_file_test_accepts_regex(self):
        instance = WhiteNoise(None, immutable_file_test='\.test$')
        self.assertTrue(instance.immutable_file_test('', '/myfile.test'))
        self.assertFalse(instance.immutable_file_test('', 'file.test.txt'))
