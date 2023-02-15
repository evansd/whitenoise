from __future__ import annotations

import sys

if sys.version_info >= (3, 11):
    from wsgiref.types import StartResponse
    from wsgiref.types import WSGIApplication
    from wsgiref.types import WSGIEnvironment
else:
    from collections.abc import Callable, Iterable, Iterator
    from types import TracebackType
    from typing import Any, Dict, Protocol, Tuple, Type, Union

    if sys.version_info >= (3, 10):
        from typing import TypeAlias
    else:
        from typing_extensions import TypeAlias

    _ExcInfo: TypeAlias = Tuple[Type[BaseException], BaseException, TracebackType]
    _OptExcInfo: TypeAlias = Union[_ExcInfo, Tuple[None, None, None]]

    class StartResponse(Protocol):
        def __call__(
            self,
            __status: str,
            __headers: list[tuple[str, str]],
            __exc_info: _OptExcInfo | None = ...,
        ) -> Callable[[bytes], object]:
            ...

    WSGIEnvironment: TypeAlias = Dict[str, Any]
    WSGIApplication: TypeAlias = Callable[
        [WSGIEnvironment, StartResponse], Iterable[bytes]
    ]

    class InputStream(Protocol):
        def read(self, __size: int = ...) -> bytes:
            ...

        def readline(self, __size: int = ...) -> bytes:
            ...

        def readlines(self, __hint: int = ...) -> list[bytes]:
            ...

        def __iter__(self) -> Iterator[bytes]:
            ...

    class ErrorStream(Protocol):
        def flush(self) -> object:
            ...

        def write(self, __s: str) -> object:
            ...

        def writelines(self, __seq: list[str]) -> object:
            ...

    class _Readable(Protocol):
        def read(self, __size: int = ...) -> bytes:
            ...

        # Optional: def close(self) -> object: ...

    class FileWrapper(Protocol):
        def __call__(
            self, __file: _Readable, __block_size: int = ...
        ) -> Iterable[bytes]:
            ...


__all__ = [
    "StartResponse",
    "WSGIApplication",
    "WSGIEnvironment",
]
