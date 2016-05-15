Change Log
==========

v3.1
----

 * Add new :any:`WHITENOISE_STATIC_PREFIX` setting to give flexibility in
   supporting non-standard deployment configurations e.g. serving the
   application somewhere other than the domain root.
 * Fix bytes/unicode bug when running with Django 1.10 on Python 2.7

v3.0
----

.. note:: The latest version of WhiteNoise contains some small **breaking changes**.
   Most users will be able to upgrade without any problems, but some
   less-used APIs have been modified:

    * The setting ``WHITENOISE_GZIP_EXCLUDE_EXTENSIONS`` has been renamed to
      ``WHITENOISE_SKIP_COMPRESS_EXTENSIONS``.
    * The CLI :ref:`compression utility <cli-utility>` has moved from ``python -m whitenoise.gzip``
      to ``python -m whitenoise.compress``.
    * The now redundant ``gzipstatic`` management command has been removed.
    * WhiteNoise no longer uses the system mimetypes files, so if you are serving
      particularly obscure filetypes you may need to add their mimetypes explicitly
      using the new :any:`mimetypes <WHITENOISE_MIMETYPES>` setting.
    * Older versions of Django (1.4-1.7) and Python (2.6) are no longer supported.
      If you need support for these platforms you can continue to use `WhiteNoise
      2.x`_.
    * The ``whitenoise.django.GzipManifestStaticFilesStorage`` storage backend
      has been moved to
      ``whitenoise.storage.CompressedManifestStaticFilesStorage``.  The old
      import path **will continue to work** for now, but users are encouraged
      to update their code to use the new path.

.. _WhiteNoise 2.x: http://whitenoise.evans.io/en/legacy-2.x/


Simpler, cleaner Django middleware integration
++++++++++++++++++++++++++++++++++++++++++++++

WhiteNoise can now integrate with Django by adding a single line to
``MIDDLEWARE_CLASSES``  without any need to edit ``wsgi.py``. This also means
that WhiteNoise plays nicely with other middleware classes such as
*SecurityMiddleware*, and that it is fully compatible with the new `Channels`_
system. See the :ref:`updated documentation <django-middleware>` for details.

.. _Channels: https://channels.readthedocs.org/en/latest/


Brotli compression support
++++++++++++++++++++++++++

`Brotli`_ is the modern, more efficient
alternative to gzip for HTTP compression. To benefit from smaller files and
faster page loads, just add the `brotlipy`_ library to your
``requirements.txt`` and WhiteNoise will take care of the rest. See the
:ref:`documentation <brotli-compression>` for details.

.. _brotli: https://en.wikipedia.org/wiki/Brotli
.. _brotlipy: http://brotlipy.readthedocs.org/en/latest/


Simpler customisation
+++++++++++++++++++++

It's now possibe to add custom headers to WhiteNoise without needing to create
a subclass, using the new :any:`add_headers_function
<WHITENOISE_ADD_HEADERS_FUNCTION>` setting.


Use WhiteNoise in development with Django
+++++++++++++++++++++++++++++++++++++++++

There's now an option to force Django to use WhiteNoise in development, rather
than its own static file handling. This results in more consistent behaviour
between development and production environments and fewer opportunities for
bugs and surprises. See the :ref:`documentation <runserver-nostatic>` for
details.



Improved mimetype handling
++++++++++++++++++++++++++

WhiteNoise now ships with its own mimetype definitions (based on those shipped
with nginx) instead of relying on the system ones, which can vary between
environments. There is a new :any:`mimetypes <WHITENOISE_MIMETYPES>`
configuration option which makes it easy to add additional type definitions if
needed.


Thanks
++++++

A big thank-you to `Ed Morley <https://github.com/edmorley>`_ and `Tim Graham
<https://github.com/timgraham>`_ for their contributions to this release.

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
