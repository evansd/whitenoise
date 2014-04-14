Using WhiteNoise with Django
============================

.. note:: To use WhiteNoise with a non-Django application see the
   :doc:`generic WSGI documentation <base>`.

This guide walks you through setting up a Django project with WhiteNoise.
In most cases it shouldn't take more than a couple of lines of configuration.

I mention Heroku in a few place as that was the initial use case which prompted me
to create WhiteNoise, but there's nothing Heroku-specific about WhiteNoise and the
instructions below should apply whatever your hosting platform.

1. Make sure *staticfiles* is configured correctly
----------------------------------------------------

If you're familiar with Django you'll know what to do. If you're just getting started
with a new Django project (v1.6 and up) then you'll need add the following to the bottom of your
``settings.py`` file:

.. code-block:: python

   STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

As part of deploying your application you'll need to run ``./manage.py collectstatic`` to
put all your static files into ``STATIC_ROOT``. (If you're running on Heroku then
this is done automatically for you.)

In your templates, make sure you're using the static_ template tag to refer
to your static files. For example:

.. code-block:: html

   {% load static from staticfiles %}
   <img src="{% static "images/hi.jpg" %}" alt="Hi!" />

.. _static: https://docs.djangoproject.com/en/1.7/ref/contrib/staticfiles/#std:templatetag-staticfiles-static


2. Enable WhiteNoise
--------------------

Edit your ``wsgi.py`` file and wrap your WSGI application like so:

.. code-block:: python

   from django.core.wsgi import get_wsgi_application
   from whitenoise.django import DjangoWhiteNoise

   application = get_wsgi_application()
   application = DjangoWhiteNoise(application)

That's it! WhiteNoise will now serve your static files. However, for anything
other than a quick demo site you'll want to proceed to step 3 and enabled gzipping
and caching.


3. Add gzip and caching support
-------------------------------

WhiteNoise comes with a storage backend which automatically takes care of gzipping
your files and creating unique names for each version so they can safely be cached
forever. To use it, just add this to your ``settings.py``:

.. code-block:: python

   STATICFILES_STORAGE = 'whitenoise.django.GzipManifestStaticFilesStorage'

This uses the new ManifestStaticFilesStorage in Django 1.7, with a backport
provided automatically for older versions of Django.


.. _cdn:

4. Use a Content-Delivery Network *(optional)*
----------------------------------------------

The above steps will get you decent performance on moderate traffic sites, however
for higher traffic sites, or sites where performance is a concern you should look
at using a CDN.

Because WhiteNoise sends appropriate cache headers with your static content, the CDN
will be able to cache your files and serve them without needing to contact your
application again.

Below are instruction for setting up WhiteNoise with Amazon CloudFront, a popular
choice of CDN. The process for other CDNs should look very similar though.

Instructions for Amazon CloudFront
++++++++++++++++++++++++++++++++++

Go to CloudFront section of the AWS Web Console, and click "Create
Distribution". Put your application's domain (without the http prefix) in the
"Origin Domain Name" field and leave the rest of the settings as they are.

It might take a few minutes for your distribution to become active. Once it's
ready, copy the distribution domain name into your ``settings.py`` file so it
looks something like this:

.. code-block:: python

   STATIC_HOST = '//d4663kmspf1sqa.cloudfront.net' if not DEBUG else ''
   STATIC_URL = STATIC_HOST + '/static/'

Or, even better, you can avoid hardcoding your CDN into your settings by doing something like this:

.. code-block:: python

   STATIC_HOST = os.environ.get('DJANGO_STATIC_HOST', '')
   STATIC_URL = STATIC_HOST + '/static/'

This way you can configure your CDN just by setting an environment variable.
For apps on Heroku, you'd run this command

.. code-block:: bash

   heroku config:set DJANGO_STATIC_HOST=//d4663kmspf1sqa.cloudfront.net


Available Settings
------------------

The DjangoWhiteNoise class takes all the same configuration options as the
WhiteNoise base class, but rather than accepting keyword arguments to its
constructor it uses Django settings. The setting names are just the keyword
arguments uppercased with a 'WHITENOISE\_' prefix.


.. attribute:: WHITENOISE_ROOT

    :default: ``None``

    Absolute path to a directory of files which will be served at the root of
    your application (ignored if not set).

    Don't use this for the bulk of your static files because you won't benefit
    from cache versioning, but it can be convenient for files like
    ``robots.txt`` or ``favicon.ico`` which you want to serve at a specific
    URL.


.. attribute:: WHITENOISE_MAX_AGE

    :default: ``60``

    Time (in seconds) for which browsers and proxies should cache **non-versioned** files.

    Versioned files (i.e. files which have been given a unique name like *base.a4ef2389.css* by
    including a hash of their contents in the name) are detected automatically and set to be
    cached forever.

    The default is chosen to be short enough not to cause problems with stale versions but
    long enough that, if you're running WhiteNoise behind a CND, the CDN will still take
    the majority of the strain during times of heavy load.


.. attribute:: WHITENOISE_CHARSET

    :default: ``settings.FILE_CHARSET`` (utf-8)

    Charset to add as part of the ``Content-Type`` header for all files whose
    mimetype allows a charset.


.. attribute:: WHITENOISE_ALLOW_ALL_ORIGINS

    :default: ``True``

    Toggles whether to send an ``Access-Control-Allow-Origin: *`` header for all
    static files.

    This allows cross-origin requests for static files which means your static files
    will continue to work as expected even if they are served via a CDN and therefore
    on a different domain. Without this your static files will *mostly* work, but you
    may have problems with fonts loading in Firefox, or accessing images in canvas
    elements, or other mysterious things.

    The W3C `explicity state`__ that this behaviour is safe for publicly
    accessible files.

.. __: http://www.w3.org/TR/cors/#security


.. attribute:: WHITENOISE_GZIP_EXCLUDE_EXTENSIONS

    :default: ``('jpg', 'jpeg', 'png', 'gif', 'webp','zip', 'gz', 'tgz', 'bz2', 'tbz', 'swf', 'flv')``

    File extensions to skip when gzipping.

    Because the gzip process will only create compressed files where this
    results in an actual size saving, it would be safe to leave this list empty
    and attempt to gzip all files. However, for files which we're confident
    won't benefit from compression, it speeds up the process if we just skip
    over them.


