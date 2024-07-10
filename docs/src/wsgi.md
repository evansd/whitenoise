# Using `ServeStatic` with WSGI apps

To enable `ServeStatic` you need to wrap your existing WSGI application in a `ServeStatic` instance and tell it where to find your static files. For example:

```python
from servestatic import ServeStatic

from my_project import MyWSGIApp

application = MyWSGIApp()
application = ServeStatic(application, root="/path/to/static/files")
application.add_files("/path/to/more/static/files", prefix="more-files/")
```

<!--shared-desc-start-->

On initialization, `ServeStatic` walks over all the files in the directories that have been added (descending into sub-directories) and builds a list of available static files. Any requests which match a static file get served by `ServeStatic`, all others are passed through to the original WSGI application.

<!--shared-desc-end-->

See the [API reference documentation](servestatic.md) for detailed usage and features.
