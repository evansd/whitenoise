WhiteNoise
==========

.. image:: https://travis-ci.org/evansd/whitenoise.png
   :target:  https://travis-ci.org/evansd/whitenoise
   :alt: Build Status
 
.. image:: https://pypip.in/v/whitenoise/badge.png
    :target: https://crate.io/packages/whitenoise/
    :alt: Latest PyPI version

WSGI middleware for easy serving of static files, with optional integration with Django.
Secure and efficient enough to use in production.

Just wrap your WSGI application in the WhiteNoise middleware, give it the path to your
static files directory and any requests matching files in that directory will be served
correctly. All other requests are passed on to your application.

Features
--------

 * Simple to configure
 * Handles caching (sends cache headers and returns Not Modified responses when appropriate)
 * Serves gzipped content (handling Accept-Encoding and Vary headers correctly)
 * Provides hooks for easy customisation, e.g. sending custom headers for certain files
 * Can serve static files from arbitrary URLs, not just from a fixed URL prefix, so
   you can use it to serve files like ``/favicon.ico`` or ``/robots.txt``
 * Python 2/3 compatibile

Shouldn't I be using a real webserver, or a CDN, or Amazon S3?
See `Infrequently Asked Questions`_


QuickStart: Standard WSGI application
-------------------------------------

.. code-block:: python

   from whitenoise import WhiteNoise

   from my_project import MyWSGIApp

   application = MyWSGIApp()
   application = WhiteNoise(application, root='/path/to/static/files')
   application.add_files('/path/to/more/static/files', prefix='more-files/')


QuickStart: Django application
------------------------------

In ``wsgi.py``:

.. code-block:: python
   
   from django.core.wsgi import get_wsgi_application
   from whitenoise.django import DjangoWhiteNoise

   application = get_wsgi_application()
   application = DjangoWhiteNoise(application)

This will automatically serve the files in ``STATIC_ROOT`` under the prefix derived from ``STATIC_URL``.

If it detects that you are using `CachedStaticFilesStorage`_ it will automatically set far-future Expires headers on
your static content.

.. _CachedStaticFilesStorage: https://docs.djangoproject.com/en/1.5/ref/contrib/staticfiles/#cachedstaticfilesstorage


QuickStart: Pre-gzipping content
--------------------------------

WhiteNoise comes with a command line utility which will create gzip-compressed versions of
files in a directory. WhiteNoise will then serve these compressed files instead, where the
client indicates that it accepts them.

.. code-block:: console

    $ python -m whitenoise.gzip --help
    usage: gzip.py [-h] [-q] [-f] root [extensions [extensions ...]]

    Search for all files inside <root> matching <extensions> and produce gzipped
    versions with a '.gz' suffix (as long this results in a smaller file.

    positional arguments:
      root         Path root from which to search for files
      extensions   File extensions to match (default: (u'css', u'js'))

    optional arguments:
      -h, --help   show this help message and exit
      -q, --quiet  Don't produce log output (default: False)
      -f, --force  Overwrite pre-existing .gz files (default: False)


There is also a Django management command which wraps this utility to gzip the contents of
your ``STATIC_ROOT`` directory. (Note that you'll need to add ``whitenoise`` to your list of
``INSTALLED_APPS`` if you want to use this command.)

.. code-block:: console

    $ python manage.py gzipstatic --help
    Usage: ./manage.py gzipstatic [options]

    Search for all files in STATIC_ROOT matching the extensions specified in
    WHITENOISE_GZIP_EXTENSIONS (by default: css, js) and produce gzipped versions
    with a '.gz' suffix

    Options:
      -v VERBOSITY, --verbosity=VERBOSITY
                            Verbosity level; 0=minimal output, 1=normal output,
                            2=verbose output, 3=very verbose output
      --settings=SETTINGS   The Python path to a settings module, e.g.
                            "myproject.settings.main". If this isn't provided, the
                            DJANGO_SETTINGS_MODULE environment variable will be
                            used.
      --pythonpath=PYTHONPATH
                            A directory to add to the Python path, e.g.
                            "/home/djangoprojects/myproject".
      --traceback           Print traceback on exception
      --quiet               Don't produce any log ouput
      --force               Overwrite pre-existing .gz files
      --version             show program's version number and exit
      -h, --help            show this help message and exit


Infrequently Asked Questions
----------------------------

Shouldn't I be using a real webserver?
++++++++++++++++++++++++++++++++++++++

Well, perhaps. Certainly something like nginx will be more efficient at serving static
files. But here are a few things to consider:

1. There are situations (e.g., when hosted on Heroku) where it's much simpler to have
   everything handled by your Python application.

2. WhiteNoise is pretty efficient. Because it only has to serve a fixed set of
   files it does as much work as it can upfront on initialization, meaning it can serve
   responses with very little work. Also, when used with gunicorn (and most other WSGI
   servers) the actual business of pushing the file down the network interface is handled
   by the kernel's highly efficient ``sendfile`` syscall, not by Python.

3. If you're using WhiteNoise behind a CDN or caching proxy (on which more below) then it
   doesn't really matter that it's not as efficient as nginx as the vast majority of
   static requests will be cached by the CDN and never touch your application.


Shouldn't I be using a CDN?
+++++++++++++++++++++++++++

Yes, given how cheap and straightforward they are these days, you probably should.
But you should be using WhiteNoise to act as the origin, or upstream, server to
your CDN.

Under this model, the CDN acts as a caching proxy which sits between your application
and the browser (only for static files, you still use your normal domain for dynamic
requests). WhiteNoise will send the appropriate cache headers so the CDN can serve
requests for static files without hitting your application.


Shouldn't I be pushing my static files to S3 using something like Django-Storages?
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

No, you shouldn't. The problem with this is that Amazon S3 cannot currently selectively serve
gzipped content to your users. Gzipping can make dramatic reductions in the bandwidth required
for your CSS and JavaScript. But while all browsers in use today can decode gzipped content, your
users may be behind crappy corporate proxies or anti-virus scanners which don't handle gzipped
content properly. Amazon S3 forces you to choose whether to serve gzipped content to no-one
(wasting bandwidth) or everyone (running the risk of your site breaking for certain users).

The correct behaviour is to examine the ``Accept-Encoding`` header of the request to see if gzip
is supported, and to return an appropriate ``Vary`` header so that intermediate caches know to do
the same thing. This is exactly what WhiteNoise does.
