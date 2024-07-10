# `ServeStaticASGI` API Reference

!!! tip

    `ServeStaticASGI` inherits its interface and features from the [WSGI variant](servestatic.md).

| Name          | Type       | Description                                                                                            | Default |
| ------------- | ---------- | ------------------------------------------------------------------------------------------------------ | ------- |
| `application` | `Callable` | Original ASGI application                                                                              | N/A     |
| `root`        | `str`      | Absolute path to a directory of static files to be served.                                             | `None`  |
| `prefix`      | `str`      | If set, the URL prefix under which the files will be served. Trailing slashes are automatically added. | `None`  |
| `**kwargs`    |            | Sets [configuration attributes](#configuration-attributes) for this instance                           | N/A     |

{% include-markdown "./servestatic.md" start="<!--shared-api-start-->" end="<!--shared-api-end-->" rewrite-relative-urls=false %}
