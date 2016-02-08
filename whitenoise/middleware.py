from __future__ import absolute_import

from django.http import (
        FileResponse, HttpResponseNotAllowed, HttpResponseNotModified)

from whitenoise.django import DjangoWhiteNoise


class WhiteNoiseMiddleware(DjangoWhiteNoise):
    """
    Wrap DjangoWhiteNoise to allow it to function as Django middleware, rather
    than WSGI middleware
    """

    def __init__(self):
        # We pass None for `application`
        super(WhiteNoiseMiddleware, self).__init__(None)

    def process_request(self, request):
        if self.autorefresh:
            static_file = self.find_file(request.path_info)
        else:
            static_file = self.files.get(request.path_info)
        if static_file is not None:
            return self.serve(static_file, request)

    def serve(self, static_file, request):
        method = request.method
        if method != 'GET' and method != 'HEAD':
            return HttpResponseNotAllowed(['GET', 'HEAD'])
        if self.file_not_modified(static_file, request.META):
            return HttpResponseNotModified()
        path, headers = self.get_path_and_headers(static_file, request.META)
        response = FileResponse(open(path, 'rb'))
        for key, value in headers.items():
            response[key] = value
        return response
