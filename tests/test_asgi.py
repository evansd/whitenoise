from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from whitenoise.asgi import AsgiWhiteNoise

from .utils import Files


@pytest.fixture()
def test_files():
    return Files(
        js=str(Path("static") / "app.js"),
    )


@pytest.fixture()
def application(test_files):
    """Return an ASGI application can serve the test files."""

    async def asgi_app(scope, receive, send):
        if scope["type"] != "http":
            raise RuntimeError("Incorrect response type!")

        await send(
            {
                "type": "http.response.start",
                "status": 404,
                "headers": [[b"content-type", b"text/plain"]],
            }
        )
        await send({"type": "http.response.body", "body": b"Not Found"})

    return AsgiWhiteNoise(asgi_app, root=test_files.directory)


class ScopeEmulator(dict):
    """Simulate a real scope."""

    def __init__(self, scope_overrides: dict | None = None):
        scope = {
            "asgi": {"version": "3.0"},
            "client": ["127.0.0.1", 64521],
            "headers": [
                (b"host", b"127.0.0.1:8000"),
                (b"connection", b"keep-alive"),
                (
                    b"sec-ch-ua",
                    b'"Not/A)Brand";v="99", "Brave";v="115", "Chromium";v="115"',
                ),
                (b"sec-ch-ua-mobile", b"?0"),
                (b"sec-ch-ua-platform", b'"Windows"'),
                (b"dnt", b"1"),
                (b"upgrade-insecure-requests", b"1"),
                (
                    b"user-agent",
                    b"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                    b" (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
                ),
                (
                    b"accept",
                    b"text/html,application/xhtml+xml,application/xml;q=0.9,image/"
                    b"avif,image/webp,image/apng,*/*;q=0.8",
                ),
                (b"sec-gpc", b"1"),
                (b"sec-fetch-site", b"none"),
                (b"sec-fetch-mode", b"navigate"),
                (b"sec-fetch-user", b"?1"),
                (b"sec-fetch-dest", b"document"),
                (b"accept-encoding", b"gzip, deflate, br"),
                (b"accept-language", b"en-US,en;q=0.9"),
            ],
            "http_version": "1.1",
            "method": "GET",
            "path": "/",
            "query_string": b"",
            "raw_path": b"/",
            "root_path": "",
            "scheme": "http",
            "server": ["127.0.0.1", 8000],
            "type": "http",
        }

        if scope_overrides:
            scope.update(scope_overrides)

        super().__init__(scope)


class ReceiveEmulator:
    """Any users awaiting on this object will be sequentially notified for each event
    that this class is initialized with."""

    def __init__(self, *events):
        self.events = list(events)

    async def __call__(self):
        return self.events.pop(0)


class SendEmulator:
    """Any events sent to this object will be stored in a list."""

    def __init__(self):
        self.events = []

    async def __call__(self, event):
        self.events.append(event)

    def __getitem__(self, index):
        return self.events[index]

    @property
    def body(self):
        """Combine all body events into a single bytestring."""
        return b"".join([event["body"] for event in self.events if event.get("body")])

    @property
    def headers(self):
        """Return the headers from the first event."""
        return dict(self[0]["headers"])

    @property
    def status(self):
        """Return the status from the first event."""
        return self[0]["status"]


def test_get_js_static_file(application, test_files):
    scope = ScopeEmulator({"path": "/static/app.js"})
    receive = ReceiveEmulator()
    send = SendEmulator()
    asyncio.run(application(scope, receive, send))
    assert send.body == test_files.js_content
    assert b"text/javascript" in send.headers[b"content-type"]
    assert send.headers[b"content-length"] == str(len(test_files.js_content)).encode()


def test_user_app(application):
    scope = ScopeEmulator({"path": "/"})
    receive = ReceiveEmulator()
    send = SendEmulator()
    asyncio.run(application(scope, receive, send))
    assert send.body == b"Not Found"
    assert b"text/plain" in send.headers[b"content-type"]
    assert send.status == 404
