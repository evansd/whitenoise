from __future__ import absolute_import, unicode_literals

import gzip
import io
import threading
import warnings
from wsgiref.simple_server import make_server, WSGIRequestHandler

import requests

warnings.filterwarnings(action='ignore', category=DeprecationWarning,
        module='requests')


class SilentWSGIHandler(WSGIRequestHandler):
    def log_message(*args):
        pass

class TestServer(object):
    """
    Wraps a WSGI application and allows you to make real HTTP
    requests against it
    """

    def __init__(self, application):
        self.application = application
        self.server = make_server('127.0.0.1', 0, application,
                handler_class=SilentWSGIHandler)

    def get(self, path, *args, **kwargs):
        url = 'http://{0[0]}:{0[1]}{1}'.format(self.server.server_address, path)
        thread = threading.Thread(target=self.server.handle_request)
        thread.start()
        response = requests.get(url, *args, **kwargs)
        thread.join()
        return response


def gzip_bytes(b):
    f = io.BytesIO()
    gz = gzip.GzipFile(fileobj=f, mode='wb')
    gz.write(b)
    gz.close()
    return f.getvalue()
