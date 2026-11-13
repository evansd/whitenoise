from __future__ import annotations

import errno
import os
import stat
from io import BytesIO

import pytest
from django.test import SimpleTestCase

from whitenoise.responders import (
    FileEntry,
    NotARegularFileError,
    Redirect,
    SlicedFile,
    StaticFile,
    parse_accept_encoding,
)


class SlicedFileTests(SimpleTestCase):
    def test_close_does_not_rerun_on_del(self):
        """
        Regression test for the subtle close() behaviour of SlicedFile that
        could lead to database connection errors.

        https://github.com/evansd/whitenoise/pull/612
        """
        file = BytesIO(b"1234567890")
        sliced_file = SlicedFile(file, 1, 2)

        # Emulate how Django patches the file object's close() method to be
        # response.close() and count the calls.
        # https://github.com/django/django/blob/345a6652e6a15febbf4f68351dcea5dd674ea324/django/core/handlers/wsgi.py#L137-L140
        calls = 0

        file_close = sliced_file.close

        def closer():
            nonlocal calls
            calls += 1
            file_close()

        sliced_file.close = closer

        sliced_file.close()
        assert calls == 1

        # Deleting the sliced file should not call close again.
        del sliced_file
        assert calls == 1


class RedirectTests(SimpleTestCase):
    def setUp(self):
        self.redirect = Redirect("dir/", headers={"Cache-Control": "max-age=60"})

    def test_without_query_string(self):
        response = self.redirect.get_response("GET", {"QUERY_STRING": ""})
        assert response.headers == [
            ("Cache-Control", "max-age=60"),
            ("Location", "dir/"),
        ]

    def test_preserves_query_string(self):
        response = self.redirect.get_response("GET", {"QUERY_STRING": "a=1&b=%20"})
        assert response.headers == [
            ("Cache-Control", "max-age=60"),
            ("Location", "dir/?a=1&b=%20"),
        ]
        assert self.redirect.get_response("GET", {}).headers[-1] == (
            "Location",
            "dir/",
        )


def _stat(size, mode=stat.S_IFREG):
    return os.stat_result((mode, 0, 0, 0, 0, 0, size, 0, 0, 0))


class StaticFileEncodingSelectionTests(SimpleTestCase):
    def setUp(self):
        self.static_file = StaticFile(
            "file.css",
            [],
            encodings={"gzip": "file.css.gz", "br": "file.css.br"},
            stat_cache={
                "file.css": _stat(1000),
                "file.css.gz": _stat(300),
                "file.css.br": _stat(200),
            },
        )

    def test_selection(self):
        cases = {
            "": "file.css",
            "*": "file.css",
            "gzip": "file.css.gz",
            "gzip, br": "file.css.br",
            "br;q=0.5, gzip": "file.css.gz",
            "gzip;q=0.5, br;q=0.5": "file.css.br",
            "gzip;q=0.5, identity": "file.css",
            "gzip, identity": "file.css.gz",
            "gzip;q=0, br;q=0": "file.css",
            "identity;q=0": "file.css",
            "zstd": "file.css",
        }
        for header, expected in cases.items():
            with self.subTest(header=header):
                path, _ = self.static_file.get_path_and_headers(
                    {"HTTP_ACCEPT_ENCODING": header}
                )
                assert path == expected


class ParseAcceptEncodingTests(SimpleTestCase):
    def test_valid(self):
        cases = {
            "": {},
            "gzip": {"gzip": 1.0},
            "GZip": {"gzip": 1.0},
            "x-gzip": {"gzip": 1.0},
            "gzip, br": {"gzip": 1.0, "br": 1.0},
            " gzip ,, br ": {"gzip": 1.0, "br": 1.0},
            "gzip;q=0.5": {"gzip": 0.5},
            "gzip ; q=1": {"gzip": 1.0},
            "gzip;Q=0.5": {"gzip": 0.5},
            "gzip;q=0, br": {"br": 1.0},
            "gzip;q=0.2, x-gzip;q=0.7": {"gzip": 0.7},
            "zstd, br;q=0.9, gzip;q=0.1": {"zstd": 1.0, "br": 0.9, "gzip": 0.1},
            "gzip;q=0.5, identity": {"gzip": 0.5, "identity": 1.0},
        }
        for header, expected in cases.items():
            with self.subTest(header=header):
                assert parse_accept_encoding(header) == expected

    def test_rejected(self):
        cases = [
            "*",
            "*;q=1",
            "gzip;q=0",
            "gzip;q=0.000",
            "gzip;q=1.5",
            "gzip;q=-1",
            "gzip;q=",
            "gzip;q=abc",
            "gzip;level=1",
        ]
        for header in cases:
            with self.subTest(header=header):
                assert parse_accept_encoding(header) == {}

    def test_unknown_codings_are_returned_whole(self):
        assert parse_accept_encoding("x-gzip-really, supergzip") == {
            "x-gzip-really": 1.0,
            "supergzip": 1.0,
        }

    def test_too_long(self):
        assert parse_accept_encoding("gzip," * 500) == {}


class FileEntryTests(SimpleTestCase):
    def test_not_a_regular_file(self):
        with pytest.raises(NotARegularFileError, match="Not a regular file"):
            FileEntry("fifo", stat_cache={"fifo": _stat(0, stat.S_IFIFO)})

    def test_unexpected_os_error_propagates(self):
        def stat_function(path):
            raise PermissionError(errno.EACCES, "Permission denied", path)

        with pytest.raises(PermissionError):
            FileEntry.stat_regular_file("file.css", stat_function)
