The documentation below is a quick-start guide to using `ServeStatic` to serve your static files. For more detailed information see the [full installation docs](django.md).

---

## Installation

Install with:

```bash linenums="0"
pip install servestatic
```

## Using with Django

Edit your `settings.py` file and add `ServeStatic` to the `MIDDLEWARE` list, above all other middleware apart from Django's [SecurityMiddleware](https://docs.djangoproject.com/en/stable/ref/middleware/#module-django.middleware.security).

```python linenums="0"
MIDDLEWARE = [
    # ...
    "django.middleware.security.SecurityMiddleware",
    "servestatic.middleware.ServeStaticMiddleware",
    # ...
]
```

That's it, you're ready to go.

Want forever-cacheable files and compression support? Just add this to your `settings.py`.

```python linenums="0"
STATICFILES_STORAGE = "servestatic.storage.CompressedManifestStaticFilesStorage"
```

For more details, including on setting up CloudFront and other CDNs see
the [full Django guide](django.md).

## Using with WSGI

To enable `ServeStatic` you need to wrap your existing WSGI application in a `ServeStatic` instance and tell it where to find your static files. For example...

```python
from servestatic import ServeStatic

from my_project import MyWSGIApp

application = MyWSGIApp()
application = ServeStatic(application, root="/path/to/static/files")
application.add_files("/path/to/more/static/files", prefix="more-files/")
```

And that's it, you're ready to go. For more details see the [full WSGI guide](wsgi.md).

## Using with ASGI

To enable `ServeStatic` you need to wrap your existing ASGI application in a `ServeStatic` instance and tell it where to find your static files. For example...

```python
from servestatic import ServeStaticASGI

from my_project import MyASGIApp

application = MyASGIApp()
application = ServeStaticASGI(application, root="/path/to/static/files")
application.add_files("/path/to/more/static/files", prefix="more-files/")
```

And that's it, you're ready to go. For more details see the [full ASGI guide](asgi.md).
