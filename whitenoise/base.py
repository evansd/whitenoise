import os
from posixpath import normpath
from wsgiref.headers import Headers
from wsgiref.util import FileWrapper

from .media_types import MediaTypes
from .scantree import scantree
from .static_file import StaticFile, MissingFileError, IsDirectoryError, Redirect
from .string_utils import (decode_if_byte_string, decode_path_info,
                           ensure_leading_trailing_slash)


class WhiteNoise(object):

    # Ten years is what nginx sets a max age if you use 'expires max;'
    # so we'll follow its lead
    FOREVER = 10*365*24*60*60

    # Attributes that can be set by keyword args in the constructor
    config_attrs = ('autorefresh', 'max_age', 'allow_all_origins', 'charset',
                    'mimetypes', 'add_headers_function', 'add_etags',
                    'index_file')
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
    # Calculate MD5-based etags for files
    add_etags = False
    # Name of index file
    index_file = None

    def __init__(self, application, root=None, prefix=None, **kwargs):
        for attr in self.config_attrs:
            try:
                value = kwargs.pop(attr)
            except KeyError:
                pass
            else:
                value = decode_if_byte_string(value)
                setattr(self, attr, value)
        if kwargs:
            raise TypeError("Unexpected keyword argument '{0}'".format(
                list(kwargs.keys())[0]))
        self.media_types = MediaTypes(extra_types=self.mimetypes)
        self.application = application
        self.files = {}
        self.directories = []
        if self.index_file is True:
            self.index_file = 'index.html'
        if root is not None:
            self.add_files(root, prefix)

    def __call__(self, environ, start_response):
        path = decode_path_info(environ['PATH_INFO'])
        if self.autorefresh:
            static_file = self.find_file(path)
        else:
            static_file = self.files.get(path)
        if static_file is None:
            return self.application(environ, start_response)
        else:
            return self.serve(static_file, environ, start_response)

    @staticmethod
    def serve(static_file, environ, start_response):
        response = static_file.get_response(environ['REQUEST_METHOD'], environ)
        status_line = '{} {}'.format(response.status, response.status.phrase)
        start_response(status_line, list(response.headers))
        if response.file is not None:
            file_wrapper = environ.get('wsgi.file_wrapper', FileWrapper)
            return file_wrapper(response.file)
        else:
            return []

    def add_files(self, root, prefix=None):
        root = decode_if_byte_string(root)
        root = root.rstrip(os.path.sep) + os.path.sep
        prefix = decode_if_byte_string(prefix)
        prefix = ensure_leading_trailing_slash(prefix)
        if self.autorefresh:
            # Later calls to `add_files` overwrite earlier ones, hence we need
            # to store the list of directories in reverse order so later ones
            # match first when they're checked in "autorefresh" mode
            self.directories.insert(0, (root, prefix))
        else:
            self.update_files_dictionary(root, prefix)

    def update_files_dictionary(self, root, prefix):
        # Build a mapping from paths to the results of `os.stat` calls
        # so we only have to touch the filesystem once
        stat_cache = dict(scantree(root))
        for path in stat_cache.keys():
            # Skip files which are just compressed versions of other files
            if path[-3:] in ('.gz', '.br') and path[:-3] in stat_cache:
                continue
            url = prefix + path[len(root):].replace('\\', '/')
            if self.index_file and url.endswith('/' + self.index_file):
                new_url = url[:-len(self.index_file)]
                self.files[url] = Redirect(new_url)
                self.files[new_url[:-1]] = Redirect(new_url)
                url = new_url
            static_file = self.get_static_file(path, url, stat_cache=stat_cache)
            self.files[url] = static_file

    def find_file(self, url):
        # Attempt to mitigate path traversal attacks. Not sure if this is
        # sufficient, hence the warning that "autorefresh" is a development
        # only feature and not for production use
        if not self.path_is_safe(url):
            return
        for root, prefix in self.directories:
            if url.startswith(prefix):
                path = os.path.join(root, url[len(prefix):])
                static_file = self.find_file_at_path(path, url)
                if static_file:
                    return static_file

    def find_file_at_path(self, path, url):
        if not self.index_file:
            try:
                return self.get_static_file(path, url)
            except MissingFileError:
                return
        else:
            if url.endswith('/'):
                path = os.path.join(path, self.index_file)
                try:
                    return self.get_static_file(path, url)
                except MissingFileError:
                    return
            elif url.endswith('/' + self.index_file):
                try:
                    self.get_static_file(path, url)
                except MissingFileError:
                    return
                else:
                    return Redirect(url[:-len(self.index_file)])
            else:
                try:
                    return self.get_static_file(path, url)
                except IsDirectoryError:
                    path = os.path.join(path, self.index_file)
                    try:
                        self.get_static_file(path, url)
                        return Redirect(url + '/')
                    except MissingFileError:
                        return
                except MissingFileError:
                    return

    def get_static_file(self, path, url, stat_cache=None):
        headers = Headers([])
        self.add_mime_headers(headers, path, url)
        self.add_cache_headers(headers, path, url)
        self.add_cors_headers(headers, path, url)
        if self.add_headers_function:
            self.add_headers_function(headers, path, url)
        return StaticFile(
                path, headers.items(),
                stat_cache=stat_cache,
                add_etag=self.add_etags,
                encodings={
                  'gzip': path + '.gz', 'brotli': path + '.br'})

    def add_mime_headers(self, headers, path, url):
        media_type = self.media_types.get_type(path)
        charset = self.get_charset(media_type, path, url)
        params = {'charset': str(charset)} if charset else {}
        headers.add_header('Content-Type', str(media_type), **params)

    def get_charset(self, media_type, path, url):
        if (media_type.startswith('text/') or
                media_type == 'application/javascript'):
            return self.charset

    def add_cache_headers(self, headers, path, url):
        if self.is_immutable_file(path, url):
            headers['Cache-Control'] = \
                    'max-age={0}, public, immutable'.format(self.FOREVER)
        elif self.max_age is not None:
            headers['Cache-Control'] = \
                    'max-age={0}, public'.format(self.max_age)

    def is_immutable_file(self, path, url):
        """
        This should be implemented by sub-classes (see e.g. DjangoWhiteNoise)
        """
        return False

    def add_cors_headers(self, headers, path, url):
        if self.allow_all_origins:
            headers['Access-Control-Allow-Origin'] = '*'

    @staticmethod
    def path_is_safe(url):
        if url == '/':
            return True
        normalised = normpath(url)
        if url.endswith('/'):
            normalised += '/'
        return normalised == url
