from __future__ import absolute_import

from django.http import FileResponse, HttpResponse

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
        response = static_file.get_response(request.method, request.META)
        status = int(response.status)
        if response.file is not None:
            http_response = FileResponse(response.file, status=status)
        else:
            http_response = HttpResponse(status=status)
        for key, value in response.headers:
            http_response[key] = value
        return http_response
