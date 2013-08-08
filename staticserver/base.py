from __future__ import absolute_import, unicode_literals

from email.utils import parsedate, formatdate
import mimetypes
import os
import re


class StaticFile(object):
    pass


class StaticServer(object):

    BLOCK_SIZE = 16 * 4096
    GZIP_SUFFIX = '.gz'
    ACCEPT_GZIP_RE = re.compile(r'\bgzip\b')

    default_max_age = None
    gzip_enabled = True

    def __init__(self, application, root, default_max_age=None, gzip_enabled=True, prefix=None):
        self.default_max_age = default_max_age
        self.gzip_enabled = gzip_enabled
        self.application = application
        self.files = self.build_files_dict(root, prefix)

    def __call__(self, environ, start_response):
        try:
            static_file = self.files[environ['PATH_INFO']]
        except KeyError:
            return self.application(environ, start_response)
        else:
            return self.serve(static_file, environ, start_response)

    def serve(self, static_file, environ, start_response):
        if self.file_not_modified(static_file, environ):
            start_response(b'304 Not Modified', [])
            return []
        if static_file.gzip_path and self.ACCEPT_GZIP_RE.search(environ.get('HTTP_ACCEPT_ENCODING', '')):
            path = static_file.gzip_path
            headers = static_file.gzip_headers
        else:
            path = static_file.path
            headers = static_file.headers
        start_response(b'200 OK', headers)
        file_wrapper = environ.get('wsgi.file_wrapper', self.yield_file)
        fileobj = open(path, 'rb')
        return file_wrapper(fileobj)

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

    def build_files_dict(self, root_path, prefix):
        prefix = (prefix or '').strip('/')
        prefix = '/{}/'.format(prefix) if prefix else '/'
        files= {}
        for dir_path, _, filenames in os.walk(root_path, followlinks=True):
            for filename in filenames:
                file_path = os.path.join(dir_path, filename)
                url = prefix + os.path.relpath(file_path, root_path)
                files[url] = self.get_file_details(file_path, url)
        if self.gzip_enabled:
            self.find_gzipped_versions(files)
        self.encode_all_headers(files)
        return files

    def get_file_details(self, file_path, url):
        static_file = StaticFile()
        static_file.path = file_path
        mimetype, encoding = mimetypes.guess_type(file_path)
        mtime = os.stat(file_path).st_mtime
        last_modified = formatdate(mtime, usegmt=True)
        static_file.last_modified = last_modified
        static_file.last_modified_parsed = parsedate(last_modified)
        static_file.headers = {
            'Content-Type': mimetype or 'application/octet-stream',
            'Last-Modified': last_modified,
        }
        if encoding:
            static_file.headers['Content-Encoding'] = encoding
        self.add_extra_headers(static_file.headers, file_path, url)
        return static_file

    def add_extra_headers(self, headers, file_path, url):
        if self.default_max_age is not None:
            headers['Cache-Control'] = 'max-age={}'.format(self.default_max_age)

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
                static_file.gzip_headers = dict(static_file.headers,
                        **{'Content-Encoding': 'gzip'})

    def encode_all_headers(self, files):
        for static_file in files.values():
            static_file.headers = self.encode_headers(static_file.headers)
            if static_file.gzip_headers:
                static_file.gzip_headers = self.encode_headers(static_file.gzip_headers)

    def encode_headers(self, headers):
        return [(k.encode('latin1'), v.encode('latin1')) for (k, v) in headers.items()]
