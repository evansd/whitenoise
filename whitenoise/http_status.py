"""
Partial backport of the `http.HTTPStatus` object from Python 3.5
"""
__all__ = ['HTTPStatus', 'STATUS_RESPONSES']

# Python 3.5
try:
    from http import HTTPStatus
    responses = None
except ImportError:
    # Python >= 3.4
    try:
        from http import client as HTTPStatus
        from http.server import BaseHTTPRequestHandler
        responses = BaseHTTPRequestHandler.responses
    # Python 2.7
    except ImportError:
        import httplib as HTTPStatus
        responses = HTTPStatus.responses


class StatusResponses(dict):

    def __missing__(self, status):
        if responses is None:
            phrase = status.phrase
        else:
            phrase = responses[status]
            if isinstance(phrase, tuple):
                phrase = phrase[0]
        value = '{} {}'.format(status, phrase)
        self[status] = value
        return value

# Map status codes to the full HTTP status line e.g. 200 => '200 OK'
STATUS_RESPONSES = StatusResponses()
