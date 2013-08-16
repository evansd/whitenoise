from __future__ import absolute_import

from email.utils import parsedate, formatdate
import mimetypes
import os
import re
from wsgiref.headers import Headers


class StaticFile(object):
    pass


class WhiteNoise(object):

    BLOCK_SIZE = 16 * 4096
    GZIP_SUFFIX = '.gz'
    ACCEPT_GZIP_RE = re.compile(r'\bgzip\b')

    default_max_age = None
    gzip_enabled = True

    def __init__(self, application, root=None, prefix=None, **kwargs):
        for attr in ('default_max_age', 'gzip_enabled'):
            setattr(self, attr, kwargs.pop(attr, getattr(self, attr)))
        if kwargs:
            raise TypeError("Unexpected keyword argument '{}'".format(
                kwargs.keys()[0]))
        self.application = application
        self.files = {}
        if root is not None:
            self.add_files(root, prefix)

    def __call__(self, environ, start_response):
        try:
            static_file = self.files[environ['PATH_INFO']]
        except KeyError:
            return self.application(environ, start_response)
        else:
            return self.serve(static_file, environ, start_response)

    def serve(self, static_file, environ, start_response):
        if self.file_not_modified(static_file, environ):
            start_response('304 Not Modified', [])
            return []
        path, headers = self.get_path_and_headers(static_file, environ)
        start_response('200 OK', headers.items())
        file_wrapper = environ.get('wsgi.file_wrapper', self.yield_file)
        fileobj = open(path, 'rb')
        return file_wrapper(fileobj)

    def get_path_and_headers(self, static_file, environ):
        if static_file.gzip_path:
            if self.ACCEPT_GZIP_RE.search(environ.get('HTTP_ACCEPT_ENCODING', '')):
                return static_file.gzip_path, static_file.gzip_headers
        return static_file.path, static_file.headers

    def file_not_modified(self, static_file, environ):
        try:
            last_request = environ['HTTP_IF_MODIFIED_SINCE']
        except KeyError:
            return False
        # Exact match, no need to parse
        if last_request == static_file.last_modified:
            return True
        return parsedate(last_request) >= static_file.last_modified_parsed

    def yield_file(self, fileobj):
        try:
            while True:
                block = fileobj.read(self.BLOCK_SIZE)
                if block:
                    yield block
                else:
                    break
        finally:
            fileobj.close()

    def add_files(self, root, prefix=None, followlinks=False):
        prefix = (prefix or '').strip('/')
        prefix = '/{}/'.format(prefix) if prefix else '/'
        new_files= {}
        for dir_path, _, filenames in os.walk(root, followlinks=followlinks):
            for filename in filenames:
                file_path = os.path.join(dir_path, filename)
                url = prefix + os.path.relpath(file_path, root)
                new_files[url] = self.get_file_details(file_path, url)
        if self.gzip_enabled:
            self.find_gzipped_versions(new_files)
        self.files.update(new_files)

    def get_file_details(self, file_path, url):
        static_file = StaticFile()
        static_file.path = file_path
        mimetype, encoding = mimetypes.guess_type(file_path)
        mtime = os.stat(file_path).st_mtime
        last_modified = formatdate(mtime, usegmt=True)
        static_file.last_modified = last_modified
        static_file.last_modified_parsed = parsedate(last_modified)
        static_file.headers = Headers([
            ('Content-Type', mimetype or 'application/octet-stream'),
            ('Last-Modified', last_modified),
        ])
        if encoding:
            static_file.headers['Content-Encoding'] = encoding
        self.add_extra_headers(static_file.headers, file_path, url)
        return static_file

    def add_extra_headers(self, headers, file_path, url):
        if self.default_max_age is not None:
            headers['Cache-Control'] = 'public, max-age={}'.format(self.default_max_age)

    def find_gzipped_versions(self, files):
        for url, static_file in files.items():
            gzip_url = url + self.GZIP_SUFFIX
            try:
                gzip_path = files[gzip_url].path
            except KeyError:
                static_file.gzip_path = None
                static_file.gzip_headers = None
            else:
                static_file.gzip_path = gzip_path
                static_file.headers['Vary'] = 'Accept-Encoding'
                static_file.gzip_headers = Headers(static_file.headers.items() + [
                        ('Content-Encoding', 'gzip')
                    ])
