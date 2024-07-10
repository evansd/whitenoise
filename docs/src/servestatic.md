# `ServeStatic` API Reference

| Name          | Type       | Description                                                                                            | Default |
| ------------- | ---------- | ------------------------------------------------------------------------------------------------------ | ------- |
| `application` | `Callable` | Original WSGI application                                                                              | N/A     |
| `root`        | `str`      | Absolute path to a directory of static files to be served.                                             | `None`  |
| `prefix`      | `str`      | If set, the URL prefix under which the files will be served. Trailing slashes are automatically added. | `None`  |
| `**kwargs`    |            | Sets [configuration attributes](#configuration-attributes) for this instance                           | N/A     |

<!--shared-api-start-->

## Configuration attributes

These can be set by passing keyword arguments to the constructor, or by sub-classing ServeStatic and setting the attributes directly.

---

### `autorefresh`

**Default:** `False`

Recheck the filesystem to see if any files have changed before responding. This is designed to be used in development where it can be convenient to pick up changes to static files without restarting the server. For both performance and security reasons, this setting should not be used in production.

---

### `max_age`

**Default:** `60`

Time (in seconds) for which browsers and proxies should cache files.

The default is chosen to be short enough not to cause problems with stale versions but long enough that, if you're running ServeStatic behind a CDN, the CDN will still take the majority of the strain during times of heavy load.

Set to `None` to disable setting any `Cache-Control` header on non-versioned files.

---

### `index_file`

**Default:** `False`

If `True` enable index file serving. If set to a non-empty string, enable index files and use that string as the index file name.

When the `index_file` option is enabled:

- Visiting `/example/` will serve the file at `/example/index.html`
- Visiting `/example` will redirect (302) to `/example/`
- Visiting `/example/index.html` will redirect (302) to `/example/`

If you want to something other than `index.html` as the index file, then you can also set this option to an alternative filename.

---

### `mimetypes`

**Default:** `None`

A dictionary mapping file extensions (lowercase) to the mimetype for that extension. For example:

```python linenums="0"
{'.foo': 'application/x-foo'}
```

Note that ServeStatic ships with its own default set of mimetypes and does not use the system-supplied ones (e.g. `/etc/mime.types`). This ensures that it behaves consistently regardless of the environment in which it's run. View the defaults in the `media_types.py` file.

In addition to file extensions, mimetypes can be specified by supplying the entire filename, for example:

```json linenums="0"
{ "some-special-file": "application/x-custom-type" }
```

---

### `charset`

**Default:** `utf-8`

Charset to add as part of the `Content-Type` header for all files whose mimetype allows a charset.

---

### `allow_all_origins`

**Default:** `True`

Toggles whether to send an `Access-Control-Allow-Origin: *` header for all static files.

This allows cross-origin requests for static files which means your static files will continue to work as expected even if they are served via a CDN and therefore on a different domain. Without this your static files will _mostly_ work, but you may have problems with fonts loading in Firefox, or accessing images in canvas elements, or other mysterious things.

The W3C [explicitly state](https://www.w3.org/TR/cors/#security) that this behaviour is safe for publicly accessible files.

---

### `add_headers_function`

**Default:** `None`

Reference to a function which is passed the headers object for each static file, allowing it to modify them.

For example...

```python
def force_download_pdfs(headers, path, url):
    """
    Args:
        headers: A wsgiref.headers instance (which you can treat \
            just as a dict) containing the headers for the current \
            file
        path: The absolute path to the local file
        url: The host-relative URL of the file e.g. \
            `/static/styles/app.css`

    Returns:
        None. Changes should be made by modifying the headers \
        dictionary directly.
    """
    if path.endswith('.pdf'):
        headers['Content-Disposition'] = 'attachment'

application = ServeStatic(
    application,
    add_headers_function=force_download_pdfs,
    )
```

---

### `immutable_file_test`

**Default:** `return False`

Reference to function, or string.

If a reference to a function, this is passed the path and URL for each static file and should return whether that file is immutable, i.e. guaranteed not to change, and so can be safely cached forever.

If a string, this is treated as a regular expression and each file's URL is matched against it.

For example...

```python
def immutable_file_test(path, url):
    """
    Args:
        path: The absolute path to the local file.
        url: The host-relative URL of the file e.g. \
            `/static/styles/app.css`

    Returns:
        bool. Whether the file is immutable.

    """
    # Match filename with 12 hex digits before the extension
    # e.g. app.db8f2edc0c8a.js
    return re.match(r'^.+\.[0-9a-f]{12}\..+$', url)
```

## Compression Support

When ServeStatic builds its list of available files it checks for corresponding files with a `.gz` and a `.br` suffix (e.g., `scripts/app.js`, `scripts/app.js.gz` and `scripts/app.js.br`). If it finds them, it will assume that they are (respectively) gzip and [brotli](https://en.wikipedia.org/wiki/Brotli) compressed versions of the original file and it will serve them in preference to the uncompressed version where clients indicate that they that compression format (see note on Amazon S3 for why this behaviour is important).

ServeStatic comes with a command line utility which will generate compressed versions of your files for you. Note that in order for brotli compression to work the [Brotli Python package](https://pypi.org/project/Brotli/) must be installed.

Usage is simple:

```console linenums="0"
$ python -m servestatic.compress --help
usage: compress.py [-h] [-q] [--no-gzip] [--no-brotli]
                   root [extensions [extensions ...]]

Search for all files inside <root> *not* matching <extensions> and produce
compressed versions with '.gz' and '.br' suffixes (as long as this results in
a smaller file)

positional arguments:
  root         Path root from which to search for files
  extensions   File extensions to exclude from compression (default: jpg,
               jpeg, png, gif, webp, zip, gz, tgz, bz2, tbz, xz, br, swf, flv,
               woff, woff2)

optional arguments:
  -h, --help   show this help message and exit
  -q, --quiet  Don't produce log output
  --no-gzip    Don't produce gzip '.gz' files
  --no-brotli  Don't produce brotli '.br' files
```

You can either run this during development and commit your compressed files to your repository, or you can run this as part of your build and deploy processes. (Note that this is handled automatically in Django if you're using the custom storage backend.)

## Caching Headers

By default, ServeStatic sets a max-age header on all responses it sends. You can configure this by passing a [`max_age`](#max_age) keyword argument.

ServeStatic sets both `Last-Modified` and `ETag` headers for all files and will return Not Modified responses where appropriate. The ETag header uses the same format as nginx which is based on the size and last-modified time of the file. If you want to use a different scheme for generating ETags you can set them via you own function by using the [`add_headers_function`](#add_headers_function) option.

Most modern static asset build systems create uniquely named versions of each file. This results in files which are immutable (i.e., they can never change their contents) and can therefore by cached indefinitely. In order to take advantage of this, ServeStatic needs to know which files are immutable. This can be done using the [`immutable_file_test`](#immutable_file_test) option which accepts a reference to a function.

The exact details of how you implement this method will depend on your particular asset build system but see the [documentation](#immutable_file_test) documentation for a simple example.

Once you have implemented this, any files which are flagged as immutable will have "cache forever" headers set.

## Using a Content Distribution Network

{% include-markdown "./django.md" start="<!--cdn-start-->" end="<!--cdn-end-->" %}

<!--shared-api-end-->
