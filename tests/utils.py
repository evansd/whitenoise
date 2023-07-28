from __future__ import annotations

import os
import threading
from wsgiref.simple_server import make_server
from wsgiref.simple_server import WSGIRequestHandler
from wsgiref.util import shift_path_info

import requests

TEST_FILE_PATH = os.path.join(os.path.dirname(__file__), "test_files")


class SilentWSGIHandler(WSGIRequestHandler):
    def log_message(*args):
        pass


class AppServer:
    """
    Wraps a WSGI application and allows you to make real HTTP
    requests against it
    """

    PREFIX = "subdir"

    def __init__(self, application):
        self.application = application
        self.server = make_server(
            "127.0.0.1", 0, self.serve_under_prefix, handler_class=SilentWSGIHandler
        )

    def serve_under_prefix(self, environ, start_response):
        prefix = shift_path_info(environ)
        if prefix != self.PREFIX:
            start_response("404 Not Found", [])
            return []
        else:
            return self.application(environ, start_response)

    def get(self, *args, **kwargs):
        return self.request("get", *args, **kwargs)

    def request(self, method, path, *args, **kwargs):
        url = "http://{0[0]}:{0[1]}{1}".format(self.server.server_address, path)
        thread = threading.Thread(target=self.server.handle_request)
        thread.start()
        response = requests.request(method, url, *args, **kwargs)
        thread.join()
        return response

    def close(self):
        self.server.server_close()


class Files:
    def __init__(self, directory="", **files):
        self.directory = os.path.join(TEST_FILE_PATH, directory)
        for name, path in files.items():
            url = f"/{AppServer.PREFIX}/{path}"
            with open(os.path.join(self.directory, path), "rb") as f:
                content = f.read()
            setattr(self, name + "_path", path)
            setattr(self, name + "_url", url)
            setattr(self, name + "_content", content)


class AsgiScopeEmulator(dict):
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


class AsgiReceiveEmulator:
    """Currently, WhiteNoise does not receive any HTTP events, so this class should
    remain functionally unused."""

    async def __call__(self):
        raise NotImplementedError("WhiteNoise received a HTTP event unexpectedly!")


class AsgiSendEmulator:
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
