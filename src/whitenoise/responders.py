from __future__ import annotations

import errno
import os
import stat
from calendar import timegm
from email.utils import formatdate, parsedate
from functools import lru_cache
from http import HTTPStatus
from io import BufferedIOBase
from types import MappingProxyType
from urllib.parse import quote
from wsgiref.headers import Headers


class Response:
    __slots__ = ("status", "headers", "file")

    def __init__(self, status, headers, file):
        self.status = status
        self.headers = headers
        self.file = file


NOT_ALLOWED_RESPONSE = Response(
    status=HTTPStatus.METHOD_NOT_ALLOWED,
    headers=[("Allow", "GET, HEAD")],
    file=None,
)

# Headers which should be returned with a 304 Not Modified response, as
# specified in https://www.rfc-editor.org/rfc/rfc9110#section-15.4.5, plus
# Access-Control-Allow-Origin so CORS checks pass on revalidation.
NOT_MODIFIED_HEADERS = (
    "Cache-Control",
    "Content-Location",
    "Date",
    "ETag",
    "Expires",
    "Vary",
    "Access-Control-Allow-Origin",
)

RANGE_NOT_SATISFIABLE_HEADERS = frozenset({"access-control-allow-origin"})


class SlicedFile(BufferedIOBase):
    """
    A file like wrapper to handle seeking to the start byte of a range request
    and to return no further output once the end byte of a range request has
    been reached.
    """

    def __init__(self, fileobj, start, end):
        fileobj.seek(start)
        self.fileobj = fileobj
        self.remaining = end - start + 1

    def read(self, size=-1):
        if self.remaining <= 0:
            return b""
        if size < 0:
            size = self.remaining
        else:
            size = min(size, self.remaining)
        data = self.fileobj.read(size)
        self.remaining -= len(data)
        return data

    def close(self):
        super().close()
        self.fileobj.close()


class StaticFile:
    __slots__ = ("last_modified", "etag", "not_modified_response", "alternatives")

    def __init__(self, path, headers, encodings=None, stat_cache=None):
        files = self.get_file_stats(path, encodings, stat_cache)
        headers = self.get_headers(headers, files)
        self.last_modified = parsedate(headers["Last-Modified"])
        self.etag = headers["ETag"]
        self.not_modified_response = self.get_not_modified_response(headers)
        self.alternatives = self.get_alternatives(headers, files)

    def get_response(self, method, request_headers):
        if method not in ("GET", "HEAD"):
            return NOT_ALLOWED_RESPONSE
        if self.is_not_modified(request_headers):
            return self.not_modified_response
        path, headers = self.get_path_and_headers(request_headers)
        if method != "HEAD":
            file_handle = open(path, "rb")  # noqa: SIM115
        else:
            file_handle = None
        range_header = request_headers.get("HTTP_RANGE")
        if range_header and self.is_if_range_satisfied(request_headers):
            try:
                return self.get_range_response(range_header, headers, file_handle)
            except ValueError:
                # If we can't interpret the Range request for any reason then
                # just ignore it and return the standard response (this
                # behaviour is allowed by the spec)
                pass
        return Response(HTTPStatus.OK, headers, file_handle)

    def get_range_response(self, range_header, base_headers, file_handle):
        headers = []
        for item in base_headers:
            if item[0] == "Content-Length":
                size = int(item[1])
            else:
                headers.append(item)
        start, end = self.get_byte_range(range_header, size)
        if start > end:
            return self.get_range_not_satisfiable_response(file_handle, size, headers)
        if file_handle is not None:
            file_handle = SlicedFile(file_handle, start, end)
        headers.append(("Content-Range", f"bytes {start}-{end}/{size}"))
        headers.append(("Content-Length", str(end - start + 1)))
        return Response(HTTPStatus.PARTIAL_CONTENT, headers, file_handle)

    def get_byte_range(self, range_header, size):
        start, end = self.parse_byte_range(range_header)
        if start < 0:
            start = max(start + size, 0)
        if end is None:
            end = size - 1
        else:
            end = min(end, size - 1)
        return start, end

    @staticmethod
    def parse_byte_range(range_header):
        units, _, range_spec = range_header.strip().partition("=")
        if units != "bytes":
            raise ValueError()
        # Only handle a single range spec. Multiple ranges will trigger a
        # ValueError below which will result in the Range header being ignored
        start_str, sep, end_str = range_spec.strip().partition("-")
        if not sep:
            raise ValueError()
        if not start_str:
            start = -int(end_str)
            end = None
        else:
            start = int(start_str)
            end = int(end_str) if end_str else None
        return start, end

    @staticmethod
    def get_range_not_satisfiable_response(file_handle, size, headers):
        if file_handle is not None:
            file_handle.close()
        response_headers = [
            (key, value)
            for key, value in headers
            if key.lower() in RANGE_NOT_SATISFIABLE_HEADERS
        ]
        response_headers.append(("Content-Range", f"bytes */{size}"))
        return Response(
            HTTPStatus.REQUESTED_RANGE_NOT_SATISFIABLE,
            response_headers,
            None,
        )

    @staticmethod
    def get_file_stats(path, encodings, stat_cache):
        # Primary file has an encoding of None
        files = {None: FileEntry(path, stat_cache)}
        if encodings:
            for encoding, alt_path in encodings.items():
                try:
                    files[encoding] = FileEntry(alt_path, stat_cache)
                except MissingFileError:
                    continue
        return files

    def get_headers(self, headers_list, files):
        headers = Headers(headers_list)
        main_file = files[None]
        if len(files) > 1:
            headers["Vary"] = "Accept-Encoding"
        if "Last-Modified" not in headers:
            mtime = main_file.mtime
            # Not all filesystems report mtimes, and sometimes they report an
            # mtime of 0 which we know is incorrect
            if mtime:
                headers["Last-Modified"] = formatdate(mtime, usegmt=True)
        if "ETag" not in headers:
            last_modified = parsedate(headers["Last-Modified"])
            if last_modified:
                timestamp = timegm(last_modified)
                headers["ETag"] = f'"{timestamp:x}-{main_file.size:x}"'
        return headers

    @staticmethod
    def get_not_modified_response(headers):
        not_modified_headers = []
        for key in NOT_MODIFIED_HEADERS:
            if key in headers:
                not_modified_headers.append((key, headers[key]))
        return Response(
            status=HTTPStatus.NOT_MODIFIED, headers=not_modified_headers, file=None
        )

    @staticmethod
    def get_alternatives(base_headers, files):
        # Sort by size so that the smallest compressed alternative matches first
        alternatives = []
        files_by_size = sorted(files.items(), key=lambda i: i[1].size)
        for encoding, file_entry in files_by_size:
            headers = Headers(base_headers.items())
            headers["Content-Length"] = str(file_entry.size)
            if encoding:
                headers["Content-Encoding"] = encoding
            alternatives.append((encoding, file_entry.path, headers.items()))
        return alternatives

    def is_not_modified(self, request_headers):
        previous_etag = request_headers.get("HTTP_IF_NONE_MATCH")
        if previous_etag is not None:
            return previous_etag == self.etag
        if self.last_modified is None:
            return False
        try:
            last_requested = request_headers["HTTP_IF_MODIFIED_SINCE"]
        except KeyError:
            return False
        last_requested_ts = parsedate(last_requested)
        if last_requested_ts is not None:
            return last_requested_ts >= self.last_modified
        return False

    def is_if_range_satisfied(self, request_headers):
        # https://www.rfc-editor.org/rfc/rfc9110#section-13.1.5
        if_range = request_headers.get("HTTP_IF_RANGE")
        if if_range is None:
            return True
        if_range = if_range.strip()
        if if_range.startswith("W/"):
            # Weak entity tags never match
            return False
        if if_range.startswith('"'):
            return if_range == self.etag
        if self.last_modified is None:
            return False
        return parsedate(if_range) == self.last_modified

    def get_path_and_headers(self, request_headers):
        accepted = parse_accept_encoding(
            request_headers.get("HTTP_ACCEPT_ENCODING", "")
        )
        # These are sorted by size so ties go to the smallest
        best = None
        best_q = -1.0
        for encoding, path, headers in self.alternatives:
            if encoding is None:
                # Serve uncompressed as a last resort, even if refused, since
                # we cannot do better.
                q = accepted.get("identity", 0.0)
            elif encoding in accepted:
                q = accepted[encoding]
            else:
                continue
            if q > best_q:
                best = (path, headers)
                best_q = q
        return best


# Recipients should treat x-gzip as equivalent to gzip:
# https://www.rfc-editor.org/rfc/rfc9110#section-8.4.1.3
coding_aliases = MappingProxyType({"x-gzip": "gzip"})


def parse_accept_encoding(accept_encoding):
    """
    Return a mapping of content codings the client accepts to their qvalues,
    per:
    https://www.rfc-editor.org/rfc/rfc9110#section-12.5.3

    Refused codings, with q=0, are omitted. The wildcard "*" is treated as
    accepting no codings.
    """
    if len(accept_encoding) > 2048:
        # Protect against DoS attacks by limiting the length we’re willing to parse
        return MappingProxyType({})

    # Content codings and parameter names are case-insensitive:
    # https://www.rfc-editor.org/rfc/rfc9110#section-8.4.1
    return _parse_accept_encoding(accept_encoding.lower())


# Browsers send a limited set of Accept-Encoding headers, so cache parsed results
@lru_cache
def _parse_accept_encoding(accept_encoding):
    accepted = {}
    for part in accept_encoding.split(","):
        stripped = part.strip()
        if not stripped:
            continue
        parsed = _parse_part(stripped)
        if parsed is not None:
            coding, q = parsed
            accepted[coding] = max(q, accepted.get(coding, 0.0))
    return MappingProxyType(accepted)


def _parse_part(part):
    if part.startswith("*"):
        return None

    if ";" not in part:
        return coding_aliases.get(part, part), 1.0

    coding, params = part.split(";", 1)
    coding = coding.strip()
    params = params.strip()
    if params.startswith("q="):
        try:
            q = float(params[2:])
        except ValueError:
            return None
        if 0 < q <= 1:
            return coding_aliases.get(coding, coding), q

    return None


class Redirect:
    __slots__ = ("headers", "location", "response")

    def __init__(self, location, headers=None):
        self.headers = list(headers.items()) if headers else []
        self.location = quote(location.encode("utf8"))
        self.response = Response(
            HTTPStatus.FOUND, [*self.headers, ("Location", self.location)], None
        )

    def get_response(self, method, request_headers):
        query_string = request_headers.get("QUERY_STRING")
        if not query_string:
            return self.response
        return Response(
            HTTPStatus.FOUND,
            [*self.headers, ("Location", f"{self.location}?{query_string}")],
            None,
        )


class NotARegularFileError(Exception):
    pass


class MissingFileError(NotARegularFileError):
    pass


class IsDirectoryError(MissingFileError):
    pass


class FileEntry:
    __slots__ = ("path", "size", "mtime")

    def __init__(self, path, stat_cache=None):
        self.path = path
        stat_function = os.stat if stat_cache is None else stat_cache.__getitem__
        stat = self.stat_regular_file(path, stat_function)
        self.size = stat.st_size
        self.mtime = stat.st_mtime

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
                raise IsDirectoryError(f"Path is a directory: {path}")
            else:
                raise NotARegularFileError(f"Not a regular file: {path}")
        return stat_result
