from __future__ import annotations

from .string_utils import decode_path_info
from whitenoise.base import BaseWhiteNoise
from whitenoise.responders import StaticFile


class AsyncWhiteNoise(BaseWhiteNoise):
    def __call__(self, scope):
        path = decode_path_info(scope["path"])

        # Determine if the request is for a static file
        static_file = None
        if scope["type"] == "http":
            if self.autorefresh:
                static_file = self.find_file(path)
            else:
                static_file = self.files.get(path)

        # If the request is for a static file, serve it
        if static_file:
            return AsyncFileServer(static_file)
        return self.application(scope)


class AsyncFileServer:
    """ASGI v3 application callable for serving static files"""

    def __init__(self, static_file: StaticFile, block_size=8192):
        # This is the same block size as wsgiref.FileWrapper
        self.block_size = block_size
        self.static_file = static_file

    async def __call__(self, scope, _receive, send):
        self.scope = scope
        self.headers = {}
        for key, value in scope["headers"]:
            wsgi_key = "HTTP_" + key.decode().upper().replace("-", "_")
            wsgi_value = value.decode()
            self.headers[wsgi_key] = wsgi_value

        response = await self.static_file.aget_response(
            self.scope["method"], self.headers
        )
        await send(
            {
                "type": "http.response.start",
                "status": response.status.value,
                "headers": [
                    (key.lower().encode(), value.encode())
                    for key, value in response.headers
                ],
            }
        )
        if response.file is None:
            await send({"type": "http.response.body", "body": b""})
        else:
            while True:
                chunk = await response.file.read(self.block_size)
                more_body = bool(chunk)
                await send(
                    {
                        "type": "http.response.body",
                        "body": chunk,
                        "more_body": more_body,
                    }
                )
                if not more_body:
                    break
