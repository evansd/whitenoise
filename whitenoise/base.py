from __future__ import absolute_import

from email.utils import parsedate, formatdate
import mimetypes
import os
import os.path
import re
from time import gmtime
from wsgiref.headers import Headers


class StaticFile(object):

    gzip_path = None

    def __init__(self, path):
        self.path = path
        self.headers = Headers([])


class WhiteNoise(object):

    BLOCK_SIZE = 16 * 4096
    GZIP_SUFFIX = '.gz'
    ACCEPT_GZIP_RE = re.compile(r'\bgzip\b')
    # All mimetypes starting 'text/' take a charset parameter, plus the
    # additions in this set
    MIMETYPES_WITH_CHARSET = frozenset((
        'application/javascript', 'application/xml'))
    # Ten years is what nginx sets a max age if you use 'expires max;'
    # so we'll follow its lead
    FOREVER = 10*365*24*60*60

    # Attributes that can be set by keyword args in the constructor
    config_attrs = ('max_age', 'allow_all_origins', 'charset')
    max_age = 60
    # Set 'Access-Control-Allow-Orign: *' header on all files.
    # As these are all public static files this is safe (See
    # http://www.w3.org/TR/cors/#security) and ensures that things (e.g
    # webfonts in Firefox) still work as expected when your static files are
    # served from a CDN, rather than your primary domain.
    allow_all_origins = True
    charset = 'utf-8'

    def __init__(self, application, root=None, prefix=None, **kwargs):
        for attr in self.config_attrs:
            try:
                setattr(self, attr, kwargs.pop(attr))
            except KeyError:
                pass
        if kwargs:
            raise TypeError("Unexpected keyword argument '{}'".format(
                list(kwargs.keys())[0]))
        self.application = application
        self.files = {}
        if root is not None:
            self.add_files(root, prefix)

    def __call__(self, environ, start_response):
        static_file = self.files.get(environ['PATH_INFO'])
        if static_file is None:
            return self.application(environ, start_response)
        else:
            return self.serve(static_file, environ, start_response)

    def serve(self, static_file, environ, start_response):
        method = environ['REQUEST_METHOD']
        if method != 'GET' and method != 'HEAD':
            start_response('405 Method Not Allowed', [('Allow', 'GET, HEAD')])
            return []
        if self.file_not_modified(static_file, environ):
            start_response('304 Not Modified', [])
            return []
        path, headers = self.get_path_and_headers(static_file, environ)
        start_response('200 OK', headers.items())
        if method == 'HEAD':
            return []
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
            last_requested = environ['HTTP_IF_MODIFIED_SINCE']
        except KeyError:
            return False
        # Exact match, no need to parse
        if last_requested == static_file.headers['Last-Modified']:
            return True
        return parsedate(last_requested) >= static_file.mtime_tuple

    def yield_file(self, fileobj):
        # Only used as a fallback in case environ doesn't supply a
        # wsgi.file_wrapper
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
        files = {}
        for dir_path, _, filenames in os.walk(root, followlinks=followlinks):
            for filename in filenames:
                file_path = os.path.join(dir_path, filename)
                url = prefix + os.path.relpath(file_path, root).replace('\\', '/')
                files[url] = self.get_static_file(file_path, url)
        self.find_gzipped_alternatives(files)
        self.files.update(files)

    def get_static_file(self, file_path, url):
        static_file = StaticFile(file_path)
        self.add_stat_headers(static_file, url)
        self.add_mime_headers(static_file, url)
        self.add_cache_headers(static_file, url)
        self.add_cors_headers(static_file, url)
        self.add_extra_headers(static_file, url)
        return static_file

    def add_stat_headers(self, static_file, url):
        stat = os.stat(static_file.path)
        static_file.mtime_tuple = gmtime(stat.st_mtime)
        static_file.headers['Last-Modified'] = formatdate(
                stat.st_mtime, usegmt=True)
        static_file.headers['Content-Length'] = str(stat.st_size)

    def add_mime_headers(self, static_file, url):
        mimetype, encoding = mimetypes.guess_type(static_file.path)
        mimetype = mimetype or 'application/octet-stream'
        charset = self.get_charset(mimetype, static_file, url)
        params = {'charset': charset} if charset else {}
        static_file.headers.add_header('Content-Type', mimetype, **params)
        if encoding:
            static_file.headers['Content-Encoding'] = encoding

    def get_charset(self, mimetype, static_file, url):
        if (mimetype.startswith('text/')
                or mimetype in self.MIMETYPES_WITH_CHARSET):
            return self.charset

    def add_cache_headers(self, static_file, url):
        if self.is_immutable_file(static_file, url):
            max_age = self.FOREVER
        else:
            max_age = self.max_age
        if max_age is not None:
            cache_control = 'public, max-age={}'.format(max_age)
            static_file.headers['Cache-Control'] = cache_control

    def is_immutable_file(self, static_file, url):
        """
        This should be implemented by sub-classes (see e.g. DjangoWhiteNoise)
        """
        return False

    def add_cors_headers(self, static_file, url):
        if self.allow_all_origins:
            static_file.headers['Access-Control-Allow-Origin'] = '*'

    def add_extra_headers(self, static_file, url):
        """
        This is provided as a hook for sub-classes, by default a no-op
        """
        pass

    def find_gzipped_alternatives(self, files):
        for url, static_file in files.items():
            gzip_url = url + self.GZIP_SUFFIX
            try:
                gzip_file = files[gzip_url]
            except KeyError:
                continue
            static_file.gzip_path = gzip_file.path
            static_file.headers['Vary'] = 'Accept-Encoding'
            # Copy the headers and add the appropriate encoding and length
            gzip_headers = Headers(static_file.headers.items())
            gzip_headers['Content-Encoding'] = 'gzip'
            gzip_headers['Content-Length'] = gzip_file.headers['Content-Length']
            static_file.gzip_headers = gzip_headers
