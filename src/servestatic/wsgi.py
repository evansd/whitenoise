from __future__ import annotations

from wsgiref.util import FileWrapper

from .base import BaseServeStatic
from .string_utils import decode_path_info


class ServeStatic(BaseServeStatic):
    def __call__(self, environ, start_response):
        path = decode_path_info(environ.get("PATH_INFO", ""))
        if self.autorefresh:
            static_file = self.find_file(path)
        else:
            static_file = self.files.get(path)
        if static_file is None:
            return self.application(environ, start_response)
        else:
            return self.serve(static_file, environ, start_response)

    @staticmethod
    def serve(static_file, environ, start_response):
        response = static_file.get_response(environ["REQUEST_METHOD"], environ)
        status_line = f"{response.status} {response.status.phrase}"
        start_response(status_line, list(response.headers))
        if response.file is not None:
            file_wrapper = environ.get("wsgi.file_wrapper", FileWrapper)
            return file_wrapper(response.file)
        else:
            return []
