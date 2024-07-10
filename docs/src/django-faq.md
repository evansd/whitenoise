## How to I use `ServeStatic` with Django Compressor?

For performance and security reasons `ServeStatic` does not check for new files after startup (unless using Django <span class="title-ref">DEBUG</span> mode). As such, all static files must be generated in advance. If you're using Django Compressor, this can be performed using its [offline compression](https://django-compressor.readthedocs.io/en/stable/usage.html#offline-compression) feature.

---

## Can I use `ServeStatic` for media files?

`ServeStatic` is not suitable for serving user-uploaded "media" files. For one thing, as described above, it only checks for static files at startup and so files added after the app starts won't be seen. More importantly though, serving user-uploaded files from the same domain as your main application is a security risk (this [blog post](https://security.googleblog.com/2012/08/content-hosting-for-modern-web.html) from Google security describes the problem well). And in addition to that, using local disk to store and serve your user media makes it harder to scale your application across multiple machines.

For all these reasons, it's much better to store files on a separate dedicated storage service and serve them to users from there. The [django-storages](https://django-storages.readthedocs.io/) library provides many options e.g. Amazon S3, Azure Storage, and Rackspace CloudFiles.

---

## How check if `ServeStatic` is working?

You can confirm that `ServeStatic` is installed and configured correctly by running you application locally with `DEBUG` disabled and checking that your static files still load.

First you need to run `collectstatic` to get your files in the right place:

```bash
python manage.py collectstatic
```

Then make sure `DEBUG` is set to `False` in your `settings.py` and start the server:

```bash
python manage.py runserver
```

You should find that your static files are served, just as they would be in production.

---

## How do I troubleshoot the `ServeStatic` storage backend?

If you're having problems with the `ServeStatic` storage backend, the chances are they're due to the underlying Django storage engine. This is because `ServeStatic` only adds a thin wrapper around Django's storage to add compression support, and because the compression code is very simple it generally doesn't cause problems.

The most common issue is that there are CSS files which reference other files (usually images or fonts) which don't exist at that specified path. When Django attempts to rewrite these references it looks for the corresponding file and throws an error if it can't find it.

To test whether the problems are due to `ServeStatic` or not, try swapping the `ServeStatic` storage backend for the Django one:

```python
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"
```

If the problems persist then your issue is with Django itself (try the [docs](https://docs.djangoproject.com/en/stable/ref/contrib/staticfiles/) or the [mailing list](https://groups.google.com/d/forum/django-users)). If the problem only occurs with ServeStatic then raise a ticket on the [issue tracker](https://github.com/Archmonger/ServeStatic/issues).

---

## Can I use `ServeStatic` with other storage backends?

`ServeStatic` will only work with storage backends that stores their files on the local filesystem in `STATIC_ROOT`. It will not work with backends that store files remotely, for instance on Amazon S3.

## Why does `ServeStatic` make my tests run slow?

`ServeStatic` is designed to do as much work as possible upfront when the application starts so that it can serve files as efficiently as possible while the application is running. This makes sense for long-running production processes, but you might find that the added startup time is a problem during test runs when application instances are frequently being created and destroyed.

The simplest way to fix this is to make sure that during testing the `SERVESTATIC_AUTOREFRESH` setting is set to `True`. (By default it is `True` when `DEBUG` is enabled and `False` otherwise.) This stops `ServeStatic` from scanning your static files on start up but other than that its behaviour should be exactly the same.

It is also worth making sure you don't have unnecessary files in your `STATIC_ROOT` directory. In particular, be careful not to include a `node_modules` directory which can contain a very large number of files and significantly slow down your application startup. If you need to include specific files from `node_modules` then you can create symlinks from within your static directory to just the files you need.

## Why do I get "ValueError: Missing staticfiles manifest entry for ..."?

If you are seeing this error that means you are referencing a static file in your templates using something like `{% static "foo" %}` which doesn't exist, or at least isn't where Django expects it to be. If you don't understand why Django can't find the file you can use

```sh
python manage.py findstatic --verbosity 2 foo
```

which will show you all the paths which Django searches for the file "foo".

If, for some reason, you want Django to silently ignore such errors you can set `SERVESTATIC_MANIFEST_STRICT` to `False`.

## How do I use `ServeStatic` with Webpack/Browserify/etc?

A simple technique for integrating any frontend build system with Django is to use a directory layout like this:

```
./static_src
        ↓
  $ ./node_modules/.bin/webpack
        ↓
./static_build
        ↓
  $ ./manage.py collectstatic
        ↓
./static_root
```

Here `static_src` contains all the source files (JS, CSS, etc) for your project. Your build tool (which can be Webpack, Browserify or whatever you choose) then processes these files and writes the output into `static_build`.

The path to the `static_build` directory is added to `settings.py`:

```python
STATICFILES_DIRS = [BASE_DIR / "static_build"]
```

This means that Django can find the processed files, but doesn't need to know anything about the tool which produced them.

The final `manage.py collectstatic` step writes "hash-versioned" and compressed copies of the static files into `static_root` ready for production.

Note, both the `static_build` and `static_root` directories should be excluded from version control (e.g. through `.gitignore`) and only the `static_src` directory should be checked in.

## How do I deploy an application which is not at the root of the domain?

Sometimes Django apps are deployed at a particular prefix (or "subdirectory") on a domain e.g. `https://example.com/my-app/` rather than just `https://example.com`.

In this case you would normally use Django's [FORCE_SCRIPT_NAME](https://docs.djangoproject.com/en/stable/ref/settings/#force-script-name) setting to tell the application where it is located. You would also need to ensure that `STATIC_URL` uses the correct prefix as well. For example:

```python
FORCE_SCRIPT_NAME = "/my-app"
STATIC_URL = FORCE_SCRIPT_NAME + "/static/"
```

If you have set these two values then `ServeStatic` will automatically configure itself correctly. If you are doing something more complex you may need to set `SERVESTATIC_STATIC_PREFIX` explicitly yourself.
