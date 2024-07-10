# Using `ServeStatic` with Django

This guide walks you through setting up a Django project with ServeStatic. In most cases it shouldn't take more than a couple of lines of configuration.

We mention Heroku in a few places, but there's nothing Heroku-specific about ServeStatic and the instructions below should apply whatever your hosting platform.

## Step 1: Enable ServeStatic

Edit your `settings.py` file and add ServeStatic to the `MIDDLEWARE` list. The ServeStatic middleware should be placed directly after the Django
[SecurityMiddleware](https://docs.djangoproject.com/en/stable/ref/middleware/#module-django.middleware.security)
(if you are using it) and before all other middleware:

```python linenums="0"
MIDDLEWARE = [
    ...,
    "django.middleware.security.SecurityMiddleware",
    "servestatic.middleware.ServeStaticMiddleware",
    ...,
]
```

That's it -- ServeStatic will now serve your static files.
However, to get the best performance you should proceed to step 3 below and enable compression and caching.

??? question "How should I order my middleware?"

    You might find other third-party middleware that suggests it should be given highest priority at the top of the middleware list. Unless you understand exactly what is happening you should ignore this advice and always place `ServeStaticMiddleware` above other middleware.

## Step 2: Add compression and caching support

ServeStatic comes with a storage backend which compresses your files and hashes them to unique names, so they can safely be cached forever. To use it, set it as your staticfiles storage backend in your settings file.

```python linenums="0"
STORAGES = {
    ...,
    "staticfiles": {
        "BACKEND": "servestatic.storage.CompressedManifestStaticFilesStorage",
    },
}
```

This combines automatic compression with the caching behaviour provided by Django's
[ManifestStaticFilesStorage](https://docs.djangoproject.com/en/stable/ref/contrib/staticfiles/#manifeststaticfilesstorage) backend. If you want to apply compression but don't want the caching behaviour then you can use the alternative backend:

```python linenums="0"
"servestatic.storage.CompressedStaticFilesStorage"
```

If you need to compress files outside of the static files storage system you can use the supplied [command line utility](servestatic.md#compression-support).

??? tip "Enable Brotli compression"

    As well as the common gzip compression format, ServeStatic supports the newer, more efficient [brotli](https://en.wikipedia.org/wiki/Brotli)
    format. This helps reduce bandwidth and increase loading speed. To enable brotli compression you will need the [Brotli Python
    package](https://pypi.org/project/Brotli/) installed by running `pip install servestatic[brotli]`.

    Brotli is supported by [all major browsers](https://caniuse.com/#feat=brotli) (except IE11). ServeStatic will only serve brotli data to browsers which request it so there are no compatibility issues with enabling brotli support.

    Also note that browsers will only request brotli data over an HTTPS connection.

## Step 3: Make sure Django's `staticfiles` is configured correctly

If you're familiar with Django you'll know what to do. If you're just getting started with a new Django project then you'll need add the following to the bottom of your `settings.py` file:

```python linenums="0"
STATIC_ROOT = BASE_DIR / "staticfiles"
```

As part of deploying your application you'll need to run `./manage.py collectstatic` to put all your static files into `STATIC_ROOT`. (If you're running on Heroku then this is done automatically for you.)

Make sure you're using the [static](https://docs.djangoproject.com/en/stable/ref/templates/builtins/#std:templatetag-static) template tag to refer to your static files, rather than writing the URL directly. For example:

```django linenums="0"
{% load static %}
<img src="{% static "images/hi.jpg" %}" alt="Hi!">

<!-- DON'T WRITE THIS -->
<img src="/static/images/hi.jpg" alt="Hi!">
```

For further details see the Django
[staticfiles](https://docs.djangoproject.com/en/stable/howto/static-files/)
guide.

---

## Optional Steps

### Configure ServeStatic

ServeStatic has a number of configuration options that you can set in your `settings.py` file.

See the [reference documentation](./django-settings.md) for a full list of options.

### Utilize a Content Delivery Network (CDN)

<!--cdn-start-->

The above steps will get you decent performance on moderate traffic sites, however for higher traffic sites, or sites where performance is a concern you should look at using a CDN.

Because ServeStatic sends appropriate cache headers with your static content, the CDN will be able to cache your files and serve them without needing to contact your application again.

Below are instruction for setting up ServeStatic with Amazon CloudFront, a popular choice of CDN. The process for other CDNs should look very similar though.

??? abstract "Configuring Amazon CloudFront"

    Go to CloudFront section of the AWS Web Console, and click "Create Distribution". Put your application's domain (without the `http` prefix) in the "Origin Domain Name" field and leave the rest of the settings as they are.

    It might take a few minutes for your distribution to become active. Once it's ready, copy the distribution domain name into your `settings.py` file so it looks something like this:

    ```python linenums="0"
    STATIC_HOST = "https://d4663kmspf1sqa.cloudfront.net" if not DEBUG else ""
    STATIC_URL = STATIC_HOST + "/static/"
    ```

    Or, even better, you can avoid hard-coding your CDN into your settings by
    doing something like this:

    ```python linenums="0"
    STATIC_HOST = os.environ.get("DJANGO_STATIC_HOST", "")
    STATIC_URL = STATIC_HOST + "/static/"
    ```

    This way you can configure your CDN just by setting an environment
    variable. For apps on Heroku, you'd run this command

    ```bash linenums="0"
    heroku config:set DJANGO_STATIC_HOST=https://d4663kmspf1sqa.cloudfront.net
    ```

??? abstract "CloudFront compression algorithms"

    By default, CloudFront will discard any `Accept-Encoding` header browsers include in requests, unless the value of the header is gzip. If it is gzip, CloudFront will fetch the uncompressed file from the origin, compress it, and return it to the requesting browser.

    To get CloudFront to not do the compression itself as well as serve files compressed using other algorithms, such as Brotli, you must configure your distribution to [cache based on the Accept-Encoding header](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/ServingCompressedFiles.html#compressed-content-custom-origin). You can do this in the `Behaviours` tab of your distribution.

??? warning "CloudFront SEO issues"

    The instructions for setting up CloudFront given above will result in the entire site being accessible via the CloudFront URL. It's possible that this can cause SEO problems if these URLs start showing up in search results. You can restrict CloudFront to only proxy your static files by following these directions:

    1.  Go to your newly created distribution and click "_Distribution Settings_", then the "_Behaviors_" tab, then "_Create Behavior_". Put `static/*` into the path pattern and click "_Create_" to save.
    2.  Now select the `Default (*)` behaviour and click "_Edit_". Set "_Restrict Viewer Access_" to "_Yes_" and then click "_Yes, Edit_" to save.
    3.  Check that the `static/*` pattern is first on the list, and the default one is second. This will ensure that requests for static files are passed through but all others are blocked.

<!--cdn-end-->

### Enable ServeStatic during development

In development Django's `runserver` automatically takes over static file handling. In most cases this is fine, however this means that some of the improvements that ServeStatic makes to static file handling won't be available in development and it opens up the possibility for differences in behaviour between development and production environments. For this reason it's a good idea to use ServeStatic in development as well.

You can disable Django's static file handling and allow ServeStatic to take over simply by passing the `--nostatic` option to the `runserver` command, but you need to remember to add this option every time you call `runserver`. An easier way is to edit your `settings.py` file and add `servestatic.runserver_nostatic` to the top of your `INSTALLED_APPS` list:

```python linenums="0"
INSTALLED_APPS = [
    ...,
    "servestatic.runserver_nostatic",
    "django.contrib.staticfiles",
    ...,
]
```
