!!! Note

    The `ServeStaticMiddleware` class takes all the same configuration options as the `ServeStatic` base class, but rather than accepting keyword arguments to its constructor it uses Django settings. The setting names are just the keyword arguments upper-cased with a `SERVESTATIC_` prefix.

---

## `SERVESTATIC_ROOT`

**Default:** `None`

Absolute path to a directory of files which will be served at the root of your application (ignored if not set).

Don't use this for the bulk of your static files because you won't benefit from cache versioning, but it can be convenient for files like `robots.txt` or `favicon.ico` which you want to serve at a specific URL.

---

## `SERVESTATIC_AUTOREFRESH`

**Default:** `settings.DEBUG`

Recheck the filesystem to see if any files have changed before responding. This is designed to be used in development where it can be convenient to pick up changes to static files without restarting the server. For both performance and security reasons, this setting should not be used in production.

---

## `SERVESTATIC_USE_FINDERS`

**Default:** `settings.DEBUG`

Instead of only picking up files collected into `STATIC_ROOT`, find and serve files in their original directories using Django's "finders" API. This is useful in development where it matches the behaviour of the old `runserver` command. It's also possible to use this setting in production, avoiding the need to run the `collectstatic` command during the build, so long as you do not wish to use any of the caching and compression features provided by the storage backends.

---

## `SERVESTATIC_MAX_AGE`

**Default:** `60 if not settings.DEBUG else 0`

Time (in seconds) for which browsers and proxies should cache **non-versioned** files.

Versioned files (i.e. files which have been given a unique name like `base.a4ef2389.css` by including a hash of their contents in the name) are detected automatically and set to be cached forever.

The default is chosen to be short enough not to cause problems with stale versions but long enough that, if you're running `ServeStatic` behind a CDN, the CDN will still take the majority of the strain during times of heavy load.

Set to `None` to disable setting any `Cache-Control` header on non-versioned files.

---

## `SERVESTATIC_INDEX_FILE`

**Default:** `False`

If `True` enable index file serving. If set to a non-empty string, enable index files and use that string as the index file name.

---

## `SERVESTATIC_MIMETYPES`

**Default:** `None`

A dictionary mapping file extensions (lowercase) to the mimetype for that extension. For example: :

```json linenums="0"
{ ".foo": "application/x-foo" }
```

Note that `ServeStatic` ships with its own default set of mimetypes and does not use the system-supplied ones (e.g. `/etc/mime.types`). This ensures that it behaves consistently regardless of the environment in which it's run. View the defaults in ServeStatic's `media_types.py` file.

In addition to file extensions, mimetypes can be specified by supplying the entire filename, for example: :

```json linenums="0"
{ "some-special-file": "application/x-custom-type" }
```

---

## `SERVESTATIC_CHARSET`

**Default:** `#!python 'utf-8'`

Charset to add as part of the `Content-Type` header for all files whose mimetype allows a charset.

---

## `SERVESTATIC_ALLOW_ALL_ORIGINS`

**Default:** `True`

Toggles whether to send an `Access-Control-Allow-Origin: *` header for all static files.

This allows cross-origin requests for static files which means your static files will continue to work as expected even if they are served via a CDN and therefore on a different domain. Without this your static files will _mostly_ work, but you may have problems with fonts loading in Firefox, or accessing images in canvas elements, or other mysterious things.

The W3C [explicitly state](https://www.w3.org/TR/cors/#security) that this behaviour is safe for publicly accessible files.

---

## `SERVESTATIC_SKIP_COMPRESS_EXTENSIONS`

**Default:** `('jpg', 'jpeg', 'png', 'gif', 'webp','zip', 'gz', 'tgz', 'bz2', 'tbz', 'xz', 'br', 'swf', 'flv', 'woff', 'woff2')`

File extensions to skip when compressing.

Because the compression process will only create compressed files where this results in an actual size saving, it would be safe to leave this list empty and attempt to compress all files. However, for files which we're confident won't benefit from compression, it speeds up the process if we just skip over them.

---

## `SERVESTATIC_ADD_HEADERS_FUNCTION`

**Default:** `None`

Reference to a function which is passed the headers object for each static file, allowing it to modify them.

The function should not return anything; changes should be made by modifying the headers dictionary directly.

For example:

```python
def force_download_pdfs(headers, path, url):
    """
    Args:
        headers: A [wsgiref.headers](https://docs.python.org/3/library/wsgiref.html#module-wsgiref.headers)\
            instance (which you can treat just as a dict) containing the headers for the current file
        path: The absolute path to the local file
        url: The host-relative URL of the file e.g. `/static/styles/app.css`

    """
    if path.endswith('.pdf'):
        headers['Content-Disposition'] = 'attachment'

SERVESTATIC_ADD_HEADERS_FUNCTION = force_download_pdfs
```

---

## `SERVESTATIC_IMMUTABLE_FILE_TEST`

**Default:** See [`immutable_file_test`](./servestatic.md#immutable_file_test) in source

Reference to function, or string.

If a reference to a function, this is passed the path and URL for each static file and should return whether that file is immutable, i.e. guaranteed not to change, and so can be safely cached forever. The default is designed to work with Django's `ManifestStaticFilesStorage` backend, and any derivatives of that, so you should only need to change this if you are using a different system for versioning your static files.

If a string, this is treated as a regular expression and each file's URL is matched against it.

Example:

```python
def immutable_file_test(path, url):
    """
    Args:
        path: The absolute path to the local file
        url: The host-relative URL of the file e.g. `/static/styles/app.css`
    """
    # Match filename with 12 hex digits before the extension
    # e.g. app.db8f2edc0c8a.js
    return re.match(r'^.+\.[0-9a-f]{12}\..+$', url)

SERVESTATIC_IMMUTABLE_FILE_TEST = immutable_file_test
```

---

## `SERVESTATIC_STATIC_PREFIX`

**Default:** Path component of `settings.STATIC_URL` (with `settings.FORCE_SCRIPT_NAME` removed if set)

The URL prefix under which static files will be served.

Usually this can be determined automatically by using the path component of `STATIC_URL`. So if `STATIC_URL` is `https://example.com/static/` then `SERVESTATIC_STATIC_PREFIX` will be `/static/`.

If your application is not running at the root of the domain and `FORCE_SCRIPT_NAME` is set then this value will be removed from the `STATIC_URL` path first to give the correct prefix.

If your deployment is more complicated than this (for instance, if you are using a CDN which is doing path rewriting) then you may need to configure this value directly.

---

## `SERVESTATIC_KEEP_ONLY_HASHED_FILES`

**Default:** `False`

Stores only files with hashed names in `STATIC_ROOT`.

By default, Django's hashed static files system creates two copies of each file in `STATIC_ROOT`: one using the original name, e.g. `app.js`, and one using the hashed name, e.g. `app.db8f2edc0c8a.js`. If `ServeStatic`'s compression backend is being used this will create another two copies of each of these files (using Gzip and Brotli compression) resulting in six output files for each input file.

In some deployment scenarios it can be important to reduce the size of the build artifact as much as possible. This setting removes the "unhashed" version of the file (which should be not be referenced in any case) which should reduce the space required for static files by half.

This setting is only effective if the `ServeStatic` storage backend is being used.

---

## `SERVESTATIC_MANIFEST_STRICT`

**Default:** `True`

Set to `False` to prevent Django throwing an error if you reference a static file which doesn't exist in the manifest. Note, if the static file does not exist, it will still throw an error.

This works by setting the [`manifest_strict`](https://docs.djangoproject.com/en/stable/ref/contrib/staticfiles/#django.contrib.staticfiles.storage.ManifestStaticFilesStorage.manifest_strict) option on the underlying Django storage instance, as described in the Django documentation:

This setting is only effective if the `ServeStatic` storage backend is being used.

!!! Note

    If a file isn't found in the `staticfiles.json` manifest at runtime, a `ValueError` is raised. This behavior can be disabled by subclassing `ManifestStaticFilesStorage` and setting the `manifest_strict` attribute to `False` -- nonexistent paths will remain unchanged.
