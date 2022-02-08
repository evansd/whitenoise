from __future__ import annotations

from whitenoise.string_utils import decode_if_byte_string, ensure_leading_trailing_slash


class DecodeIfByteStringTests:
    def test_bytes(self):
        assert decode_if_byte_string(b"abc") == "abc"

    def test_unforced(self):
        x = object()
        assert decode_if_byte_string(x) is x

    def test_forced(self):
        x = object()
        result = decode_if_byte_string(x, force_text=True)
        assert isinstance(result, str)
        assert result.startswith("<object object at ")


class EnsureLeadingTrailingSlashTests:
    def test_none(self):
        assert ensure_leading_trailing_slash(None) == "/"

    def test_empty(self):
        assert ensure_leading_trailing_slash("") == "/"

    def test_slash(self):
        assert ensure_leading_trailing_slash("/") == "/"

    def test_contents(self):
        assert ensure_leading_trailing_slash("/foo/") == "/foo/"

    def test_leading(self):
        assert ensure_leading_trailing_slash("/foo") == "/foo"

    def test_trailing(self):
        assert ensure_leading_trailing_slash("foo/") == "/foo"
