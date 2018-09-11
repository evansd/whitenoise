import os
from posixpath import normpath
import re
import warnings
from wsgiref.headers import Headers
from wsgiref.util import FileWrapper

from .media_types import MediaTypes
from .scantree import scantree
from .responders import StaticFile, MissingFileError, IsDirectoryError, Redirect
from .string_utils import (decode_if_byte_string, decode_path_info,
                           ensure_leading_trailing_slash)


class WhiteNoise(object):

    # Ten years is what nginx sets a max age if you use 'expires max;'
    # so we'll follow its lead
    FOREVER = 10*365*24*60*60

    # Attributes that can be set by keyword args in the constructor
    config_attrs = ('autorefresh', 'max_age', 'allow_all_origins', 'charset',
                    'mimetypes', 'add_headers_function', 'index_file',
                    'immutable_file_test')
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
    # Name of index file (None to disable index support)
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
        if not callable(self.immutable_file_test):
            regex = re.compile(self.immutable_file_test)
            self.immutable_file_test = lambda path, url: bool(regex.search(url))
        if root is not None:
            self.add_files(root, prefix)

    def __call__(self, environ, start_response):
        path = decode_path_info(environ.get('PATH_INFO', ''))
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
        root = decode_if_byte_string(root, force_text=True)
        root = root.rstrip(os.path.sep) + os.path.sep
        prefix = decode_if_byte_string(prefix)
        prefix = ensure_leading_trailing_slash(prefix)
        if self.autorefresh:
            # Later calls to `add_files` overwrite earlier ones, hence we need
            # to store the list of directories in reverse order so later ones
            # match first when they're checked in "autorefresh" mode
            self.directories.insert(0, (root, prefix))
        else:
            if os.path.isdir(root):
                self.update_files_dictionary(root, prefix)
            else:
                warnings.warn(u'No directory at: {}'.format(root))

    def update_files_dictionary(self, root, prefix):
        # Build a mapping from paths to the results of `os.stat` calls
        # so we only have to touch the filesystem once
        stat_cache = dict(scantree(root))
        for path in stat_cache.keys():
            relative_path = path[len(root):]
            relative_url = relative_path.replace('\\', '/')
            url = prefix + relative_url
            self.add_file_to_dictionary(url, path, stat_cache=stat_cache)

    def add_file_to_dictionary(self, url, path, stat_cache=None):
        if self.is_compressed_variant(path, stat_cache=stat_cache):
            return
        if self.index_file and url.endswith('/' + self.index_file):
            index_url = url[:-len(self.index_file)]
            index_no_slash = index_url.rstrip('/')
            self.files[url] = self.redirect(url, index_url)
            self.files[index_no_slash] = self.redirect(index_no_slash, index_url)
            url = index_url
        static_file = self.get_static_file(path, url, stat_cache=stat_cache)
        self.files[url] = static_file

    def find_file(self, url):
        # Optimization: bail early if the URL can never match a file
        if not self.index_file and url.endswith('/'):
            return
        if not self.url_is_canonical(url):
            return
        for path in self.candidate_paths_for_url(url):
            try:
                return self.find_file_at_path(path, url)
            except MissingFileError:
                pass

    def candidate_paths_for_url(self, url):
        for root, prefix in self.directories:
            if url.startswith(prefix):
                yield os.path.join(root, url[len(prefix):])

    def find_file_at_path(self, path, url):
        if self.is_compressed_variant(path):
            raise MissingFileError(path)
        if self.index_file:
            return self.find_file_at_path_with_indexes(path, url)
        else:
            return self.get_static_file(path, url)

    def find_file_at_path_with_indexes(self, path, url):
        if url.endswith('/'):
            path = os.path.join(path, self.index_file)
            return self.get_static_file(path, url)
        elif url.endswith('/' + self.index_file):
            if os.path.isfile(path):
                return self.redirect(url, url[:-len(self.index_file)])
        else:
            try:
                return self.get_static_file(path, url)
            except IsDirectoryError:
                if os.path.isfile(os.path.join(path, self.index_file)):
                    return self.redirect(url, url + '/')
        raise MissingFileError(path)

    @staticmethod
    def url_is_canonical(url):
        """
        Check that the URL path does not contain any elements which might be
        used in a path traversal attack
        """
        if '\\' in url:
            return False
        normalised = normpath(url)
        if url.endswith('/') and url != '/':
            normalised += '/'
        return normalised == url

    @staticmethod
    def is_compressed_variant(path, stat_cache=None):
        if path[-3:] in ('.gz', '.br'):
            uncompressed_path = path[:-3]
            if stat_cache is None:
                return os.path.isfile(uncompressed_path)
            else:
                return uncompressed_path in stat_cache
        return False

    def get_static_file(self, path, url, stat_cache=None):
        # Optimization: bail early if file does not exist
        if stat_cache is None and not os.path.exists(path):
            raise MissingFileError(path)
        headers = Headers([])
        self.add_mime_headers(headers, path, url)
        self.add_cache_headers(headers, path, url)
        if self.allow_all_origins:
            headers['Access-Control-Allow-Origin'] = '*'
        if self.add_headers_function:
            self.add_headers_function(headers, path, url)
        return StaticFile(
                path, headers.items(),
                stat_cache=stat_cache,
                encodings={
                  'gzip': path + '.gz', 'br': path + '.br'})

    def add_mime_headers(self, headers, path, url):
        media_type = self.media_types.get_type(path)
        if (media_type.startswith('text/') or
                media_type == 'application/javascript'):
            params = {'charset': str(self.charset)}
        else:
            params = {}
        headers.add_header('Content-Type', str(media_type), **params)

    def add_cache_headers(self, headers, path, url):
        if self.immutable_file_test(path, url):
            headers['Cache-Control'] = \
                    'max-age={0}, public, immutable'.format(self.FOREVER)
        elif self.max_age is not None:
            headers['Cache-Control'] = \
                    'max-age={0}, public'.format(self.max_age)

    def immutable_file_test(self, path, url):
        """
        This should be implemented by sub-classes (see e.g. WhiteNoiseMiddleware)
        or by setting the `immutable_file_test` config option
        """
        return False

    def redirect(self, from_url, to_url):
        """
        Return a relative 302 redirect

        We use relative redirects as we don't know the absolute URL the app is
        being hosted under
        """
        if to_url == from_url + '/':
            relative_url = from_url.split('/')[-1] + '/'
        elif from_url == to_url + self.index_file:
            relative_url = './'
        else:
            raise ValueError(
                    'Cannot handle redirect: {} > {}'.format(from_url, to_url))
        if self.max_age is not None:
            headers = {
                'Cache-Control': 'max-age={0}, public'.format(self.max_age)}
        else:
            headers = {}
        return Redirect(relative_url, headers=headers)
