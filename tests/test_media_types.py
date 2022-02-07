from __future__ import annotations

from whitenoise.media_types import MediaTypes


def test_matched_filename():
    result = MediaTypes().get_type("static/apple-app-site-association")
    assert result == "application/pkc7-mime"


def test_matched_filename_cased():
    result = MediaTypes().get_type("static/Apple-App-Site-Association")
    assert result == "application/pkc7-mime"


def test_matched_extension():
    result = MediaTypes().get_type("static/app.js")
    assert result == "text/javascript"


def test_unmatched_extension():
    result = MediaTypes().get_type("static/app.example-unmatched")
    assert result == "application/octet-stream"


def test_extra_types():
    types = MediaTypes(extra_types={".js": "application/javascript"})
    result = types.get_type("static/app.js")
    assert result == "application/javascript"
