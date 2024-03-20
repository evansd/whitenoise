class AsgiWhiteNoise:
    # This is the same block size as wsgiref.FileWrapper
    BLOCK_SIZE = 8192

    def __init__(self, whitenoise, application):
        self.whitenoise = whitenoise
        self.application = application

    async def __call__(self, scope, receive, send):
        static_file = None
        if scope["type"] == "http":
            if self.whitenoise.autorefresh:
                static_file = self.whitenoise.find_file(scope["path"])
            else:
                static_file = self.whitenoise.files.get(scope["path"])
        if static_file is None:
            await self.application(scope, receive, send)
        else:
            await receive_request(receive)
            request_headers = convert_asgi_headers(scope["headers"])
            await serve_static_file(
                send, static_file, scope["method"], request_headers, self.BLOCK_SIZE
            )


async def serve_static_file(send, static_file, method, request_headers, block_size):
    response = static_file.get_response(method, request_headers)
    try:
        await send({
            "type": "http.response.start",
            "status": response.status.value,
            "headers": convert_wsgi_headers(response.headers),
        })
        if response.file:
            # We need to only read content-length bytes instead of the whole file,
            # the difference is important when serving range requests.
            content_length = int(dict(response.headers)["Content-Length"])
            for block in read_file(response.file, content_length, block_size):
                await send({"type": "http.response.body", "body": block, "more_body": True})
        await send({"type": "http.response.body"})
    finally:
        if response.file:
            response.file.close()


async def receive_request(receive):
    more_body = True
    while more_body:
        event = await receive()
        if event["type"] != "http.request":
            raise RuntimeError(
                "Unexpected ASGI event {!r}, expected {!r}".format(event["type"], "http.request")
            )
        more_body = event.get("more_body", False)


def read_file(file_handle, content_length, block_size):
    bytes_left = content_length
    while bytes_left > 0:
        data = file_handle.read(min(block_size, bytes_left))
        if data == b"":
            raise RuntimeError("Premature end of file, expected {} more bytes".format(bytes_left))
        bytes_left -= len(data)
        yield data


def convert_asgi_headers(headers):
    return {
        "HTTP_" + name.decode().upper().replace('-', '_'): value.decode()
        for name, value in headers}


def convert_wsgi_headers(headers):
    return [(key.lower().encode(), value.encode()) for key, value in headers]
