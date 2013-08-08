StaticServer
============

**NOTE:** Very much a work in progess - no docs or tests yet

Inspired by dj-static_ and Static_ but with a slightly different approach and additional features.

.. _dj-static: https://github.com/kennethreitz/dj-static
.. _Static: http://lukearno.com/projects/static/

Benefits:
 * Python 2/3 compatibility
 * Customisable caching headers (e.g. to set cache-forever headers on certain files)
 * Serves pre-gzipped content (handling Accept-Encoding and Vary headers correctly)
 * Can serve static files from arbitrary URLs, not just stuff under ``/static`` (e.g. ``/favicon.ico`` or ``/robots.txt``)
 * Works as plain WSGI middleware, but also comes with convenient Django integration if required

A note on gzipping
------------------

If you care about serving gzipped content to your users then you should StaticServer *even if you're using Amazon CloudFront as a CDN*. The traditional approach of pushing files up to S3 and then getting CloudFront to server from there is unable to support gzipping correctly as you either have to serve gzipped content to everyone or to no-one. While all browsers today support gzip, not all proxies do especially the nasty proxies corporate users tend to be behind.

Using StaticServer, you can configure CloudFront to use your application server as its origin and it will serve up files with the appropriate cache headers so that (a) future requests get served directly from CloudFront and (b) all requests get a correctly encoded response.

Basic Django usage instructions
-------------------------------

Edit ``wsgi.py``::

    import os
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_project.settings")

    from django.core.wsgi import get_wsgi_application
    application = get_wsgi_application()

    from staticserver.django import DjangoStaticServer
    application = DjangoStaticServer(application)


To pre-gzip your JavaScript and CSS files, after running ``collectstatic`` you should run::

    python -m staticserver.gzip <path/to/static/root>
