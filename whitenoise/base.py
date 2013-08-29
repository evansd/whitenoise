from __future__ import absolute_import

from email.utils import parsedate, formatdate
import mimetypes
import os
import re
from wsgiref.headers import Headers


class StaticFile(object):
    def __init__(self, path):
        self.path = path
        self.headers = Headers([])


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
        files= {}
        for dir_path, _, filenames in os.walk(root, followlinks=followlinks):
            for filename in filenames:
                file_path = os.path.join(dir_path, filename)
                url = prefix + os.path.relpath(file_path, root)
                files[url] = self.get_static_file(file_path, url)
        if self.gzip_enabled:
            self.find_gzipped_alternatives(files)
        self.files.update(files)

    def get_static_file(self, file_path, url):
        static_file = StaticFile(file_path)
        self.add_mime_headers(static_file, url)
        self.add_last_modified_headers(static_file, url)
        self.add_cache_headers(static_file, url)
        self.add_extra_headers(static_file, url)
        return static_file

    def add_mime_headers(self, static_file, url):
        mimetype, encoding = mimetypes.guess_type(static_file.path)
        mimetype = mimetype or 'application/octet-stream'
        params = {'charset': 'utf-8'} if self.is_text_mimetype(mimetype) else {}
        static_file.headers.add_header('Content-Type', mimetype, **params)
        if encoding:
            static_file.headers['Content-Encoding'] = encoding

    def is_text_mimetype(self, mimetype):
        if mimetype.startswith('text/'):
            return True
        if mimetype == 'application/javascript':
            return True
        return False

    def add_last_modified_headers(self, static_file, url):
        mtime = os.stat(static_file.path).st_mtime
        last_modified = formatdate(mtime, usegmt=True)
        static_file.last_modified = last_modified
        static_file.last_modified_parsed = parsedate(last_modified)
        static_file.headers['Last-Modified'] = last_modified

    def add_cache_headers(self, static_file, url):
        if self.default_max_age is not None:
            cache_control = 'public, max-age={}'.format(self.default_max_age)
            static_file.headers['Cache-Control']  = cache_control

    def add_extra_headers(self, static_file, url):
        """
        This is provided as a hook for sub-classes, currently a no-op
        """
        pass

    def find_gzipped_alternatives(self, files):
        for url, static_file in files.items():
            gzip_url = url + self.GZIP_SUFFIX
            try:
                gzip_file = files[gzip_url]
            except KeyError:
                static_file.gzip_path = None
                static_file.gzip_headers = None
            else:
                static_file.gzip_path = gzip_file.path
                static_file.headers['Vary'] = 'Accept-Encoding'
                # Copy the headers and add the appropriate encoding
                static_file.gzip_headers = Headers(static_file.headers.items())
                static_file.gzip_headers['Content-Encoding'] = 'gzip'
