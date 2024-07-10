# Using `ServeStatic` with ASGI apps

!!! tip

    `ServeStaticASGI` inherits its interface and features from the [WSGI variant](wsgi.md).

To enable `ServeStatic` you need to wrap your existing ASGI application in a `ServeStatic` instance and tell it where to find your static files. For example:

```python
from servestatic import ServeStaticASGI

from my_project import MyASGIApp

application = MyWAGIApp()
application = ServeStaticASGI(application, root="/path/to/static/files")
application.add_files("/path/to/more/static/files", prefix="more-files/")
```

{% include-markdown "./wsgi.md" start="<!--shared-desc-start-->" end="<!--shared-desc-end-->" %}

See the [API reference documentation](servestatic-asgi.md) for detailed usage and features.
