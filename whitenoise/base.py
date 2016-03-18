from email.utils import parsedate, formatdate
import os
from posixpath import normpath
import re
from wsgiref.headers import Headers

from .media_types import MediaTypes
from .utils import (ensure_leading_trailing_slash, MissingFileError,
                    stat_regular_file)


class StaticFile(object):

    def __init__(self, plain_file=None, gzip_file=None, brotli_file=None,
                 last_modified=None):
        self.plain_file = plain_file
        self.gzip_file = gzip_file
        self.brotli_file = brotli_file
        self.last_modified = last_modified


class WhiteNoise(object):

    BLOCK_SIZE = 16 * 4096
    ACCEPT_GZIP_RE = re.compile(r'\bgzip\b')
    ACCEPT_BROTLI_RE = re.compile(r'\bbr\b')
    # Ten years is what nginx sets a max age if you use 'expires max;'
    # so we'll follow its lead
    FOREVER = 10*365*24*60*60

    # Attributes that can be set by keyword args in the constructor
    config_attrs = ('autorefresh', 'max_age', 'allow_all_origins', 'charset',
                    'mimetypes', 'add_headers_function')
    # Re-check the filesystem on every request so that any changes are
    # automatically picked up. NOTE: For use in development only, not supported
    # in production
    autorefresh = False
    max_age = 60
    # Set 'Access-Control-Allow-Orign: *' header on all files.
    # As these are all public static files this is safe (See
    # http://www.w3.org/TR/cors/#security) and ensures that things (e.g
    # webfonts in Firefox) still work as expected when your static files are
    # served from a CDN, rather than your primary domain.
    allow_all_origins = True
    charset = 'utf-8'
    # Custom mime types
    mimetypes = None
    # Callback for adding custom logic when setting headers
    add_headers_function = None

    def __init__(self, application, root=None, prefix=None, **kwargs):
        for attr in self.config_attrs:
            try:
                setattr(self, attr, kwargs.pop(attr))
            except KeyError:
                pass
        if kwargs:
            raise TypeError("Unexpected keyword argument '{0}'".format(
                list(kwargs.keys())[0]))
        self.media_types = MediaTypes(extra_types=self.mimetypes)
        self.application = application
        self.files = {}
        self.directories = []
        if root is not None:
            self.add_files(root, prefix)

    def __call__(self, environ, start_response):
        if self.autorefresh:
            static_file = self.find_file(environ['PATH_INFO'])
        else:
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
        accept_encoding = environ.get('HTTP_ACCEPT_ENCODING', '')
        if static_file.brotli_file:
            if self.ACCEPT_BROTLI_RE.search(accept_encoding):
                return static_file.brotli_file
        if static_file.gzip_file:
            if self.ACCEPT_GZIP_RE.search(accept_encoding):
                return static_file.gzip_file
        return static_file.plain_file

    def file_not_modified(self, static_file, environ):
        try:
            last_requested = environ['HTTP_IF_MODIFIED_SINCE']
        except KeyError:
            return False
        return parsedate(last_requested) >= static_file.last_modified

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

    def add_files(self, root, prefix=None):
        prefix = ensure_leading_trailing_slash(prefix)
        if self.autorefresh:
            # Later calls to `add_files` overwrite earlier ones, hence we need
            # to store the list of directories in reverse order so later ones
            # match first when they're checked in "autorefresh" mode
            self.directories.insert(0, (root, prefix))
        else:
            self.update_files_dictionary(root, prefix)

    def update_files_dictionary(self, root, prefix):
        for directory, _, filenames in os.walk(root, followlinks=True):
            for filename in filenames:
                path = os.path.join(directory, filename)
                url = prefix + os.path.relpath(path, root).replace('\\', '/')
                self.files[url] = self.get_static_file(path, url)

    def find_file(self, url):
        # Don't bother checking URLs which could only ever be directories
        if not url or url[-1] == '/':
            return
        # Attempt to mitigate path traversal attacks. Not sure if this is
        # sufficient, hence the warning that "autorefresh" is a development
        # only feature and not for production use
        if normpath(url) != url:
            return
        for root, prefix in self.directories:
            if url.startswith(prefix):
                path = os.path.join(root, url[len(prefix):])
                try:
                    return self.get_static_file(path, url)
                except MissingFileError:
                    pass

    def get_static_file(self, path, url):
        headers = Headers([])
        self.add_stat_headers(headers, path, url)
        self.add_mime_headers(headers, path, url)
        self.add_cache_headers(headers, path, url)
        self.add_cors_headers(headers, path, url)
        self.add_extra_headers(headers, path, url)
        if self.add_headers_function:
            self.add_headers_function(headers, path, url)
        last_modified = parsedate(headers['Last-Modified'])
        gzip_file = self.get_alternative_encoding(headers, path, '.gz', 'gzip')
        brotli_file = self.get_alternative_encoding(headers, path, '.br', 'br')
        return StaticFile(plain_file=(path, headers),
                          gzip_file=gzip_file,
                          brotli_file=brotli_file,
                          last_modified=last_modified)

    def add_stat_headers(self, headers, path, url):
        file_stat = stat_regular_file(path)
        headers['Last-Modified'] = formatdate(file_stat.st_mtime, usegmt=True)
        headers['Content-Length'] = str(file_stat.st_size)

    def add_mime_headers(self, headers, path, url):
        media_type = self.media_types.get_type(path)
        charset = self.get_charset(media_type, path, url)
        params = {'charset': charset} if charset else {}
        headers.add_header('Content-Type', media_type, **params)

    def get_charset(self, media_type, path, url):
        if (media_type.startswith('text/') or
                media_type == 'application/javascript'):
            return self.charset

    def add_cache_headers(self, headers, path, url):
        if self.is_immutable_file(path, url):
            max_age = self.FOREVER
        else:
            max_age = self.max_age
        if max_age is not None:
            cache_control = 'public, max-age={0}'.format(max_age)
            headers['Cache-Control'] = cache_control

    def is_immutable_file(self, path, url):
        """
        This should be implemented by sub-classes (see e.g. DjangoWhiteNoise)
        """
        return False

    def add_cors_headers(self, headers, path, url):
        if self.allow_all_origins:
            headers['Access-Control-Allow-Origin'] = '*'

    def add_extra_headers(self, headers, path, url):
        """
        This is provided as a hook for sub-classes, by default a no-op
        """
        pass

    def get_alternative_encoding(self, headers, path, suffix, encoding):
        alt_path = path + suffix
        try:
            alt_size = stat_regular_file(alt_path).st_size
        except MissingFileError:
            return None
        headers['Vary'] = 'Accept-Encoding'
        alt_headers = Headers(headers.items())
        alt_headers['Content-Encoding'] = encoding
        alt_headers['Content-Length'] = str(alt_size)
        return alt_path, alt_headers
