from __future__ import annotations

import asyncio

from asgiref.compatibility import guarantee_single_callable

from .string_utils import decode_path_info
from whitenoise.base import BaseWhiteNoise

# This is the same size as wsgiref.FileWrapper
BLOCK_SIZE = 8192


class AsgiWhiteNoise(BaseWhiteNoise):
    async def __call__(self, scope, receive, send):
        # Ensure ASGI v2 is converted to ASGI v3
        # This technically could be done in __init__, but it would break type hints
        if not getattr(self, "guarantee_single_callable", False):
            self.application = guarantee_single_callable(self.application)
            self.guarantee_single_callable = True

        # Determine if the request is for a static file
        path = decode_path_info(scope["path"])
        static_file = None
        if scope["type"] == "http":
            if self.autorefresh and hasattr(asyncio, "to_thread"):
                # Use a thread while searching disk for files on Python 3.9+
                static_file = await asyncio.to_thread(self.find_file, path)
            elif self.autorefresh:
                static_file = self.find_file(path)
            else:
                static_file = self.files.get(path)

        # Serve static file if it exists
        if static_file:
            await AsgiFileServer(static_file)(scope, receive, send)
            return

        # Serve the user's ASGI application
        await self.application(scope, receive, send)


class AsgiFileServer:
    """Simple ASGI application that streams a StaticFile over HTTP."""

    def __init__(self, static_file):
        self.static_file = static_file

    async def __call__(self, scope, receive, send):
        # Convert ASGI headers into WSGI headers. Allows us to reuse WSGI header logic
        # inside of aget_response().
        headers = {}
        for key, value in scope["headers"]:
            wsgi_key = "HTTP_" + key.decode().upper().replace("-", "_")
            wsgi_value = value.decode()
            headers[wsgi_key] = wsgi_value

        response = await self.static_file.aget_response(scope["method"], headers)

        # Send out the file response in chunks
        await send(
            {
                "type": "http.response.start",
                "status": response.status,
                "headers": [
                    (key.lower().encode(), value.encode())
                    for key, value in response.headers
                ],
            }
        )

        # Head requests have no body
        if response.file is None:
            await send({"type": "http.response.body", "body": b""})
            return

        # Stream the file response body
        async with response.file as async_file:
            while True:
                chunk = await async_file.read(BLOCK_SIZE)
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
