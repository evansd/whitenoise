Change Log
==========

development
-----------

.. note:: The latest version of WhiteNoise contains some small **breaking changes**.
   Most users will be able to upgrade without any problems, but some
   less-used APIs have been modified:

    * The setting ``WHITENOISE_GZIP_EXCLUDE_EXTENSIONS`` has been renamed to
      ``WHITENOISE_SKIP_COMPRESS_EXTENSIONS``.
    * The CLI :ref:`compression utility <cli-utility>` has moved from ``python -m whitenoise.gzip``
      to ``python -m whitenoise.compress``.
    * WhiteNoise no longer uses the system mimetypes files, so if you are serving
      particularly obscure filetypes you may need to add their mimetypes explicitly
      using the new :any:`mimetypes <WHITENOISE_MIMETYPES>` setting.
    * Older versions of Django (1.4-1.7) and Python (2.6) are no longer supported.
      If you need support for these platforms you can continue to use `WhiteNoise
      2.x`_.

.. _WhiteNoise 2.x: http://whitenoise.evans.io/en/legacy-2.x/


Django middleware integration
+++++++++++++++++++++++++++++

WhiteNoise can now integrate with Django by adding a single line to
``MIDDLEWARE_CLASSES``  without any need to edit ``wsgi.py``. This also means
that WhiteNoise plays nicely with other middleware classes such as
`SecurityMiddleware`_. See the :ref:`updated documentation <django-middleware>`
for details.

.. _SecurityMiddleware: https://docs.djangoproject.com/en/stable/ref/middleware/#module-django.middleware.security


Brotli compression support
++++++++++++++++++++++++++

Brotli is the modern, more efficient alternative to gzip for HTTP compression. To benefit
from smaller files and faster page loads, just add the ``brotlipy`` library to your
``requirements.txt`` and WhiteNoise will take care of the rest.

Brotli is supported by Firefox and will shortly be available in Chrome.

Simpler customisation
+++++++++++++++++++++

...

Use WhiteNoise in development with Django
+++++++++++++++++++++++++++++++++++++++++

...

---------------------------

v2.0.6
------
* Rebuild with latest version of `wheel` to get `extras_require` support.


v2.0.5
------
* Add missing argparse dependency for Python 2.6 (thanks @movermeyer)).


v2.0.4
------
* Report path on MissingFileError (thanks @ezheidtmann).


v2.0.3
------
* Add `__version__` attribute.


v2.0.2
------
* More helpful error message when STATIC_URL is set to the root of a domain (thanks @dominicrodger).


v2.0.1
------
* Add support for Python 2.6.
* Add a more helpful error message when attempting to import DjangoWhiteNoise before `DJANGO_SETTINGS_MODULE` is defined.


v2.0
------
* Add an `autorefresh` mode which picks up changes to static files made after application startup (for use in development).
* Add a `use_finders` mode for DjangoWhiteNoise which finds files in their original directories without needing them collected in `STATIC_ROOT` (for use in development). Note, this is only useful if you don't want to use Django's default runserver behaviour.
* Remove the `follow_symlinks` argument from `add_files` and now always follow symlinks.
* Support extra mimetypes which Python doesn't know about by default (including .woff2 format)
* Some internal refactoring. Note, if you subclass WhiteNoise to add custom behaviour you may need to make some small changes to your code.


v1.0.6
------
* Fix unhelpful exception inside `make_helpful_exception` on Python 3 (thanks @abbottc).


v1.0.5
------
* Fix error when attempting to gzip empty files (thanks @ryanrhee).


v1.0.4
------
* Don't attempt to gzip ``.woff`` files as they're already compressed.
* Base decision to gzip on compression ratio achieved, so we don't incur gzip overhead just to save a few bytes.
* More helpful error message from ``collectstatic`` if CSS files reference missing assets.


v1.0.3
------
* Fix bug in Last Modified date handling (thanks to Atsushi Odagiri for spotting).


v1.0.2
------
* Set the default max_age parameter in base class to be what the docs claimed it was.


v1.0.1
------
* Fix path-to-URL conversion for Windows.
* Remove cruft from packaging manifest.


v1.0
----
* First stable release.
