"""
Very partial backport of the `http.HTTPStatus` enum from Python 3.5

This implements just enough of the interface for our purposes, it does not
attempt to be a full implementation.
"""


class HTTPStatus(int):

    phrase = None

    def __new__(cls, code, phrase):
        instance = int.__new__(cls, code)
        instance.phrase = phrase
        return instance


HTTPStatus.OK = HTTPStatus(200, "OK")
HTTPStatus.PARTIAL_CONTENT = HTTPStatus(206, "Partial Content")
HTTPStatus.FOUND = HTTPStatus(302, "Found")
HTTPStatus.NOT_MODIFIED = HTTPStatus(304, "Not Modified")
HTTPStatus.METHOD_NOT_ALLOWED = HTTPStatus(405, "Method Not Allowed")
HTTPStatus.REQUESTED_RANGE_NOT_SATISFIABLE = HTTPStatus(416, "Range Not Satisfiable")
