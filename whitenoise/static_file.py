from collections import namedtuple
from email.utils import formatdate, parsedate
import errno
import hashlib
try:
    from http import HTTPStatus
except ImportError:
    from .httpstatus_backport import HTTPStatus
import mimetypes
import mmap
import os
import re
import stat
from wsgiref.headers import Headers


Response = namedtuple('Response', ('status', 'headers', 'file'))

NOT_ALLOWED_RESPONSE = Response(
        status=HTTPStatus.METHOD_NOT_ALLOWED,
        headers=[('Allow', 'GET, HEAD')],
        file=None)

# Headers which should be returned with a 304 Not Modified response as
# specified here: http://tools.ietf.org/html/rfc7232#section-4.1
NOT_MODIFIED_HEADERS = ('Cache-Control', 'Content-Location', 'Date', 'ETag',
                        'Expires', 'Vary')


class StaticFile(object):

    def __init__(self, path, headers, encodings=None, stat_cache=None,
            add_etag=False):
        files = self.get_file_stats(path, encodings, stat_cache)
        headers = self.get_headers(headers, files, add_etag=add_etag)
        self.last_modified = parsedate(headers['Last-Modified'])
        self.etag = headers.get('ETag')
        self.not_modified_response = self.get_not_modified_response(headers)
        self.alternatives = self.get_alternatives(headers, files)

    def get_response(self, method, request_headers):
        if method not in ('GET', 'HEAD'):
            return NOT_ALLOWED_RESPONSE
        if self.is_not_modified(request_headers):
            return self.not_modified_response
        path, headers = self.get_path_and_headers(request_headers)
        if method != 'HEAD':
            file_handle = open(path, 'rb')
        else:
            file_handle = None
        return Response(HTTPStatus.OK, headers, file_handle)

    @staticmethod
    def get_file_stats(path, encodings, stat_cache):
        files = {None: File(path, stat_cache)}
        if encodings:
            for encoding, alt_path in encodings.items():
                try:
                    files[encoding] = File(alt_path, stat_cache)
                except MissingFileError:
                    continue
        return files

    def get_headers(self, headers, files, add_etag=False):
        headers = Headers(headers)
        primary_file = files[None]
        if len(files) > 1:
            headers['Vary'] = 'Accept-Encoding'
        if 'Last-Modified' not in headers:
            mtime = primary_file.stat.st_mtime
            headers['Last-Modified'] = formatdate(mtime, usegmt=True)
        if 'Content-Type' not in headers:
            self.set_content_type(headers, primary_file.path)
        if add_etag and 'ETag' not in headers:
            headers['ETag'] = self.calculate_etag(primary_file)
        return headers

    @staticmethod
    def set_content_type(headers, path):
        content_type, encoding = mimetypes.guess_type(path)
        content_type = content_type or 'application/octet-stream'
        headers['Content-Type'] = content_type
        if encoding:
            headers['Content-Encoding'] = encoding

    @staticmethod
    def calculate_etag(file_item):
        # Windows won't allow an empty mapping so we handle zero-sized
        # files here
        if file_item.stat.st_size == 0:
            return hashlib.md5('').hexdigest()
        with open(file_item.path, 'rb') as f:
            mmapped_file = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
            try:
                hashobj = hashlib.md5(mmapped_file)
            finally:
                mmapped_file.close()
        return hashobj.hexdigest()

    @staticmethod
    def get_not_modified_response(headers):
        not_modified_headers = []
        for key in NOT_MODIFIED_HEADERS:
            if key in headers:
                not_modified_headers.append((key, headers[key]))
        return Response(
                status=HTTPStatus.NOT_MODIFIED,
                headers=not_modified_headers,
                file=None)

    @staticmethod
    def get_alternatives(base_headers, files):
        alternatives = []
        files_by_size = sorted(files.items(), key=lambda i: i[1].stat.st_size)
        for encoding, file_item in files_by_size:
            headers = Headers(base_headers.items())
            headers['Content-Length'] = str(file_item.stat.st_size)
            if encoding:
                headers['Content-Encoding'] = encoding
                encoding_re = re.compile(r'\b%s\b' % encoding)
            else:
                encoding_re = re.compile('')
            alternatives.append((encoding_re, file_item.path, headers.items()))
        return alternatives

    def is_not_modified(self, request_headers):
        if self.etag_matches(request_headers):
            return True
        return self.not_modified_since(request_headers)

    def etag_matches(self, request_headers):
        if not self.etag:
            return False
        return self.etag == request_headers.get('IF_NONE_MATCH')

    def not_modified_since(self, request_headers):
        try:
            last_requested = request_headers['HTTP_IF_MODIFIED_SINCE']
        except KeyError:
            return False
        return parsedate(last_requested) >= self.last_modified

    def get_path_and_headers(self, request_headers):
        accept_encoding = request_headers.get('HTTP_ACCEPT_ENCODING', '')
        for encoding_re, path, headers in self.alternatives:
            if encoding_re.search(accept_encoding):
                return path, headers


class NotARegularFileError(Exception):
    pass


class MissingFileError(NotARegularFileError):
    pass


class IsDirectoryError(MissingFileError):
    pass


class File(object):

    def __init__(self, path, stat_cache):
        stat_function = os.stat if stat_cache is None else stat_cache.__getitem__
        self.stat = self.stat_regular_file(path, stat_function)
        self.path = path

    @staticmethod
    def stat_regular_file(path, stat_function):
        """
        Wrap `stat_function` to raise appropriate errors if `path` is not a
        regular file
        """
        try:
            stat_result = stat_function(path)
        except KeyError:
            raise MissingFileError(path)
        except OSError as e:
            if e.errno in (errno.ENOENT, errno.ENAMETOOLONG):
                raise MissingFileError(path)
            else:
                raise
        if not stat.S_ISREG(stat_result.st_mode):
            if stat.S_ISDIR(stat_result.st_mode):
                raise IsDirectoryError(u'Path is a directory: {0}'.format(path))
            else:
                raise NotARegularFileError(u'Not a regular file: {0}'.format(path))
        return stat_result
