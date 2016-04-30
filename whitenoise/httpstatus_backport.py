"""
Very partial backport of the `http.HTTPStatus` enum from Python 3.5

This implements just enough of the interface for our purposes, it does not
attempt to be a full implementation.
"""
# Python 3.0 - 3.4
try:
    from http import client as status_module
    from http.server import BaseHTTPRequestHandler
    responses = BaseHTTPRequestHandler.responses
# Python 2.7
except ImportError:
    import httplib as status_module
    responses = status_module.responses


class HTTPStatusValue(int):

    phrase = None

    def __new__(cls, code, phrase):
        instance = int.__new__(cls, code)
        instance.phrase = phrase
        return instance


class HTTPStatusProxy(object):

    def __getattr__(self, status):
        code = getattr(status_module, status)
        phrase = responses[code]
        if isinstance(phrase, tuple):
            phrase = phrase[0]
        value = HTTPStatusValue(code, phrase)
        setattr(self, status, value)
        return value


HTTPStatus = HTTPStatusProxy()
