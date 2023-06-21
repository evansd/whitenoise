from __future__ import annotations

from whitenoise.string_utils import ensure_leading_trailing_slash


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
