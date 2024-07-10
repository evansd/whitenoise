from __future__ import annotations

from .asgi import ServeStaticASGI
from .wsgi import ServeStatic

__all__ = ["ServeStaticASGI", "ServeStatic"]
