from __future__ import annotations

from asgiref.compatibility import guarantee_single_callable

from whitenoise.base import BaseWhiteNoise
from whitenoise.responders import StaticFile

from .string_utils import decode_path_info


class AsyncWhiteNoise(BaseWhiteNoise):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.application = guarantee_single_callable(self.application)

    async def __call__(self, scope, receive, send):
        path = decode_path_info(scope["path"])

        # Determine if the request is for a static file
        static_file = None
        if scope["type"] == "http":
            if self.autorefresh:
                static_file = self.find_file(path)
            else:
                static_file = self.files.get(path)

        # Serving static files
        if static_file:
            await AsgiFileServer(static_file)(scope, receive, send)

        # Serving the user's ASGI application
        else:
            await self.application(scope, receive, send)


class AsgiFileServer:
    """ASGI v3 application callable for serving static files"""

    def __init__(self, static_file: StaticFile, block_size=8192):
        # This is the same block size as wsgiref.FileWrapper
        self.block_size = block_size
        self.static_file = static_file

    async def __call__(self, scope, receive, send):
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
