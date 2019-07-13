Change Log
==========

.. |br| raw:: html

   <br />

v4.1.3
------

 * Fix handling of zero-valued mtimes which can occur when running on some
   filesystems (thanks `@twosigmajab <https://github.com/twosigmajab>`_ for
   reporting).
 * Fix potential path traversal attack while running in autorefresh mode on
   Windows (thanks `@phith0n <https://github.com/phith0n>`_ for reporting).
   This is a good time to reiterate that autofresh mode is never intended for
   production use.


v4.1.2
------

 * Add correct MIME type for WebAssembly, which is required for files to be
   executed (thanks `@mdboom <https://github.com/mdboom>`_ ).
 * Stop accessing the FILE_CHARSET Django setting which was almost entirely
   unused and is now deprecated (thanks `@timgraham
   <https://github.com/timgraham>`_).


v4.1.1
------

 * Fix `bug <https://github.com/evansd/whitenoise/issues/202>`_ in ETag
   handling (thanks `@edmorley <https://github.com/edmorley>`_).
 * Documentation fixes (thanks `@jamesbeith <https://github.com/jamesbeith>`_
   and `@mathieusteele <https://github.com/mathieusteele>`_).


v4.1
----

 * Silenced spurious warning about missing directories when in development (i.e
   "autorefresh") mode.
 * Support supplying paths as `Pathlib
   <https://docs.python.org/3.4/library/pathlib.html>`_ instances, rather than
   just strings (thanks `@browniebroke <https://github.com/browniebroke>`_).
 * Add a new :ref:`CompressedStaticFilesStorage <compression-and-caching>`
   backend to support applying compression without applying Django's hash-versioning
   process.
 * Documentation improvements.


v4.0
----

.. note:: **Breaking changes**
          The latest version of WhiteNoise removes some options which were
          deprecated in the previous major release:

    * The WSGI integration option for Django
      (which involved editing ``wsgi.py``) has been removed. Instead, you
      should add WhiteNoise to your
      middleware list in ``settings.py`` and remove any reference to WhiteNoise from
      ``wsgi.py``.
      See the :ref:`documentation <django-middleware>` for more details. |br|
      (The :doc:`pure WSGI <base>` integration is still available for non-Django apps.)

    * The ``whitenoise.django.GzipManifestStaticFilesStorage`` alias has now
      been removed. Instead you should use the correct import path:
      ``whitenoise.storage.CompressedManifestStaticFilesStorage``.

    If you are not using either of these integration options you should have
    no issues upgrading to the latest version.

Removed Python 3.3 Support
++++++++++++++++++++++++++

Removed support for Python 3.3 since it's end of life was in September 2017.


Index file support
++++++++++++++++++

WhiteNoise now supports serving :ref:`index files <index-files-django>` for
directories (e.g. serving ``/example/index.html`` at ``/example/``). It also
creates redirects so that visiting the index file directly, or visiting the URL
without a trailing slash will redirect to the correct URL.


Range header support ("byte serving")
+++++++++++++++++++++++++++++++++++++

WhiteNoise now respects the HTTP Range header which allows a client to request
only part of a file. The main use for this is in serving video files to iOS
devices as Safari refuses to play videos unless the server supports the
Range header.


ETag support
++++++++++++

WhiteNoise now adds ETag headers to files using the same algorithm used by
nginx. This gives slightly better caching behaviour than relying purely on Last
Modified dates (although not as good as creating immutable files using
something like ``ManifestStaticFilesStorage``, which is still the best option
if you can use it).

If you need to generate your own ETags headers for any reason you can define a
custom :any:`add_headers_function <WHITENOISE_ADD_HEADERS_FUNCTION>`.


Remove requirement to run collectstatic
+++++++++++++++++++++++++++++++++++++++

By setting :any:`WHITENOISE_USE_FINDERS` to ``True`` files will be served
directly from their original locations (usually in ``STATICFILES_DIRS`` or app
``static`` subdirectories) without needing to be collected into ``STATIC_ROOT``
by the collectstatic command. This was
always the default behaviour when in ``DEBUG`` mode but previously it wasn't
possible to enable this behaviour in production. For small apps which aren't
using the caching and compression features of the more advanced storage
backends this simplifies the deployment process by removing the need to run
collectstatic as part of the build step -- in fact, it's now possible not to
have any build step at all.


Customisable immutable files test
+++++++++++++++++++++++++++++++++

WhiteNoise ships with code which detects when you are using Django's
ManifestStaticFilesStorage backend and sends optimal caching headers for files
which are guaranteed not to change. If you are using a different system for
generating cacheable files then you might need to supply your own function for
detecting such files. Previously this required subclassing WhiteNoise, but now
you can use the :any:`WHITENOISE_IMMUTABLE_FILE_TEST` setting.


Fix runserver_nostatic to work with Channels
++++++++++++++++++++++++++++++++++++++++++++

The old implementation of :ref:`runserver_nostatic <runserver-nostatic>` (which
disables Django's default static file handling in development) did not work
with `Channels`_, which needs its own runserver implementation. The
runserver_nostatic command has now been rewritten so that it should work with
Channels and with any other app which provides its own runserver.

.. _Channels: https://channels.readthedocs.io/


Reduced storage requirements for static files
+++++++++++++++++++++++++++++++++++++++++++++

The new :any:`WHITENOISE_KEEP_ONLY_HASHED_FILES` setting reduces the number of
files in STATIC_ROOT by half by storing files only under their hashed names
(e.g.  ``app.db8f2edc0c8a.js``), rather than also keeping a copy with the
original name (e.g. ``app.js``).



Improved start up performance
+++++++++++++++++++++++++++++

When in production mode (i.e. when :any:`autorefresh <WHITENOISE_AUTOREFRESH>`
is disabled), WhiteNoise scans all static files when the application starts in
order to be able to serve them as efficiently and securely as possible. For
most applications this makes no noticeable difference to start up time, however
for applications with very large numbers of static files this process can take
some time. In WhiteNoise 4.0 the file scanning code has been rewritten to do
the minimum possible amount of filesystem access which should make the start up
process considerably faster.


Windows Testing
+++++++++++++++

WhiteNoise has always aimed to support Windows as well as \*NIX platforms but
we are now able to run the test suite against Windows as part of the CI process
which should ensure that we can maintain Windows compatibility in future.


Modification times for compressed files
+++++++++++++++++++++++++++++++++++++++

The compressed storage backend (which generates Gzip and Brotli compressed
files) now ensures that compressed files have the same modification time as the
originals.  This only makes a difference if you are using the compression
backend with something other than WhiteNoise to actually serve the files, which
very few users do.

Replaced brotlipy with official Brotli Python Package
+++++++++++++++++++++++++++++++++++++++++++++++++++++

Since the official `Brotli project <https://github.com/google/brotli>`_ offers
a `Brotli Python package <https://pypi.org/project/Brotli/>`_ brotlipy has been
replaced with Brotli.

Furthermore a ``brotli`` key has been added to ``extras_require`` which allows
installing WhiteNoise and Brotli together like this:

.. code-block:: bash

    pip install whitenoise[brotli]


---------------------------

v3.3.1
------

 * Fix issue with the immutable file test when running behind a CDN which rewrites
   paths (thanks @lskillen).

v3.3.0
------

 * Support the new `immutable <https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Cache-Control#Revalidation_and_reloading>`_
   Cache-Control header. This gives better caching behaviour for immutable resources than
   simply setting a large max age.

v3.2.3
------

 * Gracefully handle invalid byte sequences in URLs.
 * Gracefully handle filenames which are too long for the filesystem.
 * Send correct Content-Type for Adobe's ``crossdomain.xml`` files.

v3.2.2
------

 * Convert any config values supplied as byte strings to text to avoid
   runtime encoding errors when encountering non-ASCII filenames.

v3.2.1
------

 * Handle non-ASCII URLs correctly when using the ``wsgi.py`` integration.
 * Fix exception triggered when a static files "finder" returned a directory
   rather than a file.

v3.2
----

 * Add support for the new-style middleware classes introduced in Django 1.10.
   The same WhiteNoiseMiddleware class can now be used in either the old
   ``MIDDLEWARE_CLASSES`` list or the new ``MIDDLEWARE`` list.
 * Fixed a bug where incorrect Content-Type headers were being sent on 304 Not
   Modified responses (thanks `@oppianmatt <https://github.com/oppianmatt>`_).
 * Return Vary and Cache-Control headers on 304 responses, as specified by the
   `RFC <http://tools.ietf.org/html/rfc7232#section-4.1>`_.

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

.. _Channels: https://channels.readthedocs.io/


Brotli compression support
++++++++++++++++++++++++++

`Brotli`_ is the modern, more efficient alternative to gzip for HTTP
compression. To benefit from smaller files and faster page loads, just install
the `brotlipy`_ library, update your ``requirements.txt`` and WhiteNoise
will take care of the rest. See the :ref:`documentation <brotli-compression>`
for details.

.. _brotli: https://en.wikipedia.org/wiki/Brotli
.. _brotlipy: https://brotlipy.readthedocs.io/


Simpler customisation
+++++++++++++++++++++

It's now possible to add custom headers to WhiteNoise without needing to create
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
