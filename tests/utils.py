from __future__ import annotations

import os
import threading
from wsgiref.simple_server import WSGIRequestHandler
from wsgiref.simple_server import make_server
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
    def __init__(self, directory, **files):
        self.directory = os.path.join(TEST_FILE_PATH, directory)
        for name, path in files.items():
            url = f"/{AppServer.PREFIX}/{path}"
            with open(os.path.join(self.directory, path), "rb") as f:
                content = f.read()
            setattr(self, name + "_path", path)
            setattr(self, name + "_url", url)
            setattr(self, name + "_content", content)
