from __future__ import annotations

import asyncio

from asgiref.compatibility import guarantee_single_callable

from .string_utils import decode_path_info
from servestatic.base import BaseServeStatic

# This is the same size as wsgiref.FileWrapper
BLOCK_SIZE = 8192


class ServeStaticASGI(BaseServeStatic):
    user_app = None

    async def __call__(self, scope, receive, send):
        # Ensure ASGI v2 is converted to ASGI v3
        if not self.user_app:
            self.user_app = guarantee_single_callable(self.application)

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
        await self.user_app(scope, receive, send)


class AsgiFileServer:
    """Simple ASGI application that streams a StaticFile over HTTP in chunks."""

    def __init__(self, static_file):
        self.static_file = static_file

    async def __call__(self, scope, receive, send):
        # Convert ASGI headers into WSGI headers. Allows us to reuse all of our WSGI
        # header logic inside of aget_response().
        wsgi_headers = {
            "HTTP_" + key.decode().upper().replace("-", "_"): value.decode()
            for key, value in scope["headers"]
        }

        # Get the ServeStatic file response
        response = await self.static_file.aget_response(scope["method"], wsgi_headers)

        # Start a new HTTP response for the file
        await send(
            {
                "type": "http.response.start",
                "status": response.status,
                "headers": [
                    # Convert headers back to ASGI spec
                    (key.lower().encode(), value.encode())
                    for key, value in response.headers
                ],
            }
        )

        # Head responses have no body, so we terminate early
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
