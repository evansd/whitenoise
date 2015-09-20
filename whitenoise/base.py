from __future__ import absolute_import

from email.utils import parsedate, formatdate
import errno
from mimetypes import MimeTypes
import os
import os.path
from posixpath import normpath
import re
import stat
from wsgiref.headers import Headers


class NotARegularFileError(Exception): pass
class MissingFileError(NotARegularFileError): pass


def configure_mimetypes(extra_types):
    """
    Add additional mimetypes to a local MimeTypes instance to avoid polluting
    global registery
    """
    mimetypes = MimeTypes()
    for content_type, extension in extra_types:
        mimetypes.add_type(content_type, extension)
    return mimetypes



def stat_regular_file(path):
    """
    Wrap os.stat to raise appropriate errors if `path` is not a regular file
    """
    try:
        file_stat = os.stat(path)
    except OSError as e:
        if e.errno == errno.ENOENT:
            raise MissingFileError(path)
        else:
            raise
    if not stat.S_ISREG(file_stat.st_mode):
        # We ignore directories and treat them as missing files
        if stat.S_ISDIR(file_stat.st_mode):
            raise MissingFileError()
        else:
            raise NotARegularFileError('Not a regular file: {0}'.format(path))
    return file_stat


def format_prefix(prefix):
    prefix = (prefix or '').strip('/')
    return '/{0}/'.format(prefix) if prefix else '/'


class StaticFile(object):

    def __init__(self, path, headers, last_modified,
            gzip_path=None,
            gzip_headers=None):
        self.path = path
        self.headers = headers
        self.last_modified = last_modified
        self.gzip_path = gzip_path
        self.gzip_headers = gzip_headers


class WhiteNoise(object):

    BLOCK_SIZE = 16 * 4096
    GZIP_SUFFIX = '.gz'
    ACCEPT_GZIP_RE = re.compile(r'\bgzip\b')
    EXTRA_MIMETYPES = (
            ('font/woff2', '.woff2'),)
    # All mimetypes starting 'text/' take a charset parameter, plus the
    # additions in this set
    MIMETYPES_WITH_CHARSET = frozenset((
        'application/javascript', 'application/xml'))
    # Ten years is what nginx sets a max age if you use 'expires max;'
    # so we'll follow its lead
    FOREVER = 10*365*24*60*60

    # Attributes that can be set by keyword args in the constructor
    config_attrs = ('autorefresh', 'max_age', 'allow_all_origins', 'charset')
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

    def __init__(self, application, root=None, prefix=None, **kwargs):
        for attr in self.config_attrs:
            try:
                setattr(self, attr, kwargs.pop(attr))
            except KeyError:
                pass
        if kwargs:
            raise TypeError("Unexpected keyword argument '{0}'".format(
                list(kwargs.keys())[0]))
        self.mimetypes = configure_mimetypes(self.EXTRA_MIMETYPES)
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
        if static_file.gzip_path:
            if self.ACCEPT_GZIP_RE.search(environ.get('HTTP_ACCEPT_ENCODING', '')):
                return static_file.gzip_path, static_file.gzip_headers
        return static_file.path, static_file.headers

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
        prefix = format_prefix(prefix)
        # Later calls to `add_files` overwrite earlier ones, hence we need to
        # store the list of directories in reverse order so later ones match first
        # when they're checked in "autorefresh" mode
        self.directories.insert(0, (root, prefix))
        # We still scan the directory in "autorefresh" mode even though this is wasted
        # work because we want to ensure that any exceptions that will occur in
        # production mode still get triggered
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
        last_modified = parsedate(headers['Last-Modified'])
        gzip_path, gzip_headers = self.get_gzipped_alternative(headers, path)
        return StaticFile(path, headers, last_modified, gzip_path, gzip_headers)

    def add_stat_headers(self, headers, path, url):
        file_stat = stat_regular_file(path)
        headers['Last-Modified'] = formatdate(file_stat.st_mtime, usegmt=True)
        headers['Content-Length'] = str(file_stat.st_size)

    def add_mime_headers(self, headers, path, url):
        mimetype, encoding = self.mimetypes.guess_type(path)
        mimetype = mimetype or 'application/octet-stream'
        charset = self.get_charset(mimetype, path, url)
        params = {'charset': charset} if charset else {}
        headers.add_header('Content-Type', mimetype, **params)
        if encoding:
            headers['Content-Encoding'] = encoding

    def get_charset(self, mimetype, path, url):
        if (mimetype.startswith('text/')
                or mimetype in self.MIMETYPES_WITH_CHARSET):
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

    def get_gzipped_alternative(self, headers, path):
        gzip_path = path + self.GZIP_SUFFIX
        try:
            gzip_size = stat_regular_file(gzip_path).st_size
        except MissingFileError:
            gzip_path = None
            gzip_headers = None
        else:
            headers['Vary'] = 'Accept-Encoding'
            gzip_headers = Headers(headers.items())
            gzip_headers['Content-Encoding'] = 'gzip'
            gzip_headers['Content-Length'] = str(gzip_size)
        return gzip_path, gzip_headers
