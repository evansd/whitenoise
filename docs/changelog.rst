=========
Changelog
=========

6.8.2 (2024-10-29)
------------------

* Fix compression speed gains for the thread pool when running Django’s ``collectstatic``.
  The thread pool had no effect due to use of a generator for the results, a refactoring introduced when reviewing the initial PR.

  Thanks to Petr Přikryl for the investigation and fix in `PR #616 <https://github.com/evansd/whitenoise/pull/616>`__.

6.8.1 (2024-10-28)
------------------

* Raise any errors from threads in the ``whitenoise.compress`` command.

  Regression in 6.8.0.
  Thanks to Tom Grainger for the spotting this with a `comment on PR #484 <https://github.com/evansd/whitenoise/pull/484#discussion_r1818989096>`__.

6.8.0 (2024-10-28)
------------------

* Drop Django 3.2 to 4.1 support.

* Drop Python 3.8 support.

* Support Python 3.13.

* Fix a bug introduced in version 6.0.0 where ``Range`` requests could lead to database connection errors in other requests.

  Thanks to Per Myren for the detailed investigation and fix in `PR #612 <https://github.com/evansd/whitenoise/pull/612>`__.

* Use Django’s |FORCE_SCRIPT_NAME|__ setting correctly.
  This reverts a change from version 5.3.0 that added a call to Django’s |get_script_prefix() method|__ outside of the request-response cycle.

  .. |FORCE_SCRIPT_NAME| replace:: ``FORCE_SCRIPT_NAME``
  __ https://docs.djangoproject.com/en/stable/ref/settings/#std:setting-FORCE_SCRIPT_NAME

  .. |get_script_prefix() method| replace:: ``get_script_prefix()`` method
  __ https://docs.djangoproject.com/en/stable/ref/urlresolvers/#django.urls.get_script_prefix

  Thanks to Sarah Boyce in `PR #486 <https://github.com/evansd/whitenoise/pull/486>`__.

* Compress files using a thread pool.
  This speeds up the compression step up to four times in benchmarks.

  Thanks to Anthony Ricaud in `PR #484 <https://github.com/evansd/whitenoise/pull/484>`__.

6.7.0 (2024-06-19)
------------------

* Support Django 5.1.

6.6.0 (2023-10-11)
------------------

* Support Django 5.0.

* Drop Python 3.7 support.

6.5.0 (2023-06-16)
------------------

* Support Python 3.12.

* Changed documentation site URL from ``https://whitenoise.evans.io/`` to ``https://whitenoise.readthedocs.io/``.

6.4.0 (2023-02-25)
------------------

* Support Django 4.2.

* Remove further support for byte strings from the ``root`` and ``prefix`` arguments to ``WhiteNoise``, and Django’s ``STATIC_ROOT`` setting.
  Like in the previous release, this seems to be a remnant of Python 2 support.
  Again, this change may be backwards incompatible for a small number of projects, but it’s unlikely.
  Django does not support ``STATIC_ROOT`` being a byte string.

6.3.0 (2023-01-03)
------------------

* Add some video file extensions to be ignored during compression.
  Since such files are already heavily compressed, further compression rarely helps.

  Thanks to Jon Ribbens in `PR #431 <https://github.com/evansd/whitenoise/pull/431>`__.

* Remove the behaviour of decoding byte strings passed for settings that take strings.
  This seemed to be left around from supporting Python 2.
  This change may be backwards incompatible for a small number of projects.

* Document “hidden” feature of setting ``max_age`` to ``None`` to disable the ``Cache-Control`` header.

* Drop support for working as old-style Django middleware, as support was `removed in Django 2.0 <https://docs.djangoproject.com/en/dev/releases/2.0/#features-removed-in-2-0>`__.

6.2.0 (2022-06-05)
------------------

* Support Python 3.11.

* Support Django 4.1.

6.1.0 (2022-05-10)
------------------

* Drop support for Django 2.2, 3.0, and 3.1.

6.0.0 (2022-02-10)
------------------

* Drop support for Python 3.5 and 3.6.

* Add support for Python 3.9 and 3.10.

* Drop support for Django 1.11, 2.0, and 2.1.

* Add support for Django 4.0.

* Import new MIME types from Nginx, changes:

  - ``.avif`` files are now served with the ``image/avif`` MIME type.

  - Open Document files with extensions ``.odg``, ``.odp``, ``.ods``, and ``.odt`` are now served with their respective ``application/vnd.oasis.opendocument.*`` MIME types.

* The ``whitenoise.__version__`` attribute has been removed.
  Use ``importlib.metadata.version()`` to check the version of Whitenoise if you need to.

* Requests using the ``Range`` header can no longer read beyond the end of the requested range.

  Thanks to Richard Tibbles in `PR #322 <https://github.com/evansd/whitenoise/pull/322>`__.

* Treat empty and ``"*"`` values for ``Accept-Encoding`` as if the client doesn’t support any encoding.

  Thanks to Richard Tibbles in `PR #323 <https://github.com/evansd/whitenoise/pull/323>`__.

5.3.0 (2021-07-16)
------------------

* Gracefully handle unparsable ``If-Modified-Since`` headers (thanks `@danielegozzi <https://github.com/danielegozzi>`_).

* Test against Django 3.2 (thanks `@jhnbkr <https://github.com/jhnbkr>`_).

* Add mimetype for Markdown (``.md``) files (thanks `@bz2 <https://github.com/bz2>`_).

* Various documentation improvements (thanks `@PeterJCLaw <https://github.com/PeterJCLaw>`_ and `@AliRn76 <https://github.com/AliRn76>`_).

5.2.0 (2020-08-04)
------------------

* Add support for `relative STATIC_URLs <https://docs.djangoproject.com/en/3.1/ref/settings/#std:setting-STATIC_URL>`_ in settings, as allowed in Django 3.1.

* Add mimetype for ``.mjs`` (JavaScript module) files and use recommended ``text/javascript`` mimetype for ``.js`` files (thanks `@hanswilw <https://github.com/hanswilw>`_).

* Various documentation improvements (thanks `@lukeburden <https://github.com/lukeburden>`_).

5.1.0 (2020-05-20)
------------------

* Add a :any:`manifest_strict <WHITENOISE_MANIFEST_STRICT>` setting to prevent Django throwing errors when missing files are referenced (thanks `@MegacoderKim <https://github.com/MegacoderKim>`_).

5.0.1 (2019-12-12)
------------------

* Fix packaging to indicate only Python 3.5+ compatibiity (thanks `@mdalp <https://github.com/mdalp>`_).

5.0 (2019-12-10)
----------------

.. note:: This is a major version bump, but only because it removes Python 2
   compatibility. If you were already running under Python 3 then there should
   be no breaking changes.

   WhiteNoise is now tested on Python 3.5--3.8 and Django 2.0--3.0.

Other changes include:

* Fix incompatibility with Django 3.0 which caused problems with Safari (details `here <https://github.com/evansd/whitenoise/issues/240>`_).
  Thanks `@paltman <https://github.com/paltman>`_ and `@giilby <https://github.com/giilby>`_ for diagnosing.

* Lots of improvements to the test suite (including switching to py.test).
  Thanks `@NDevox <https://github.com/ndevox>`_ and `@Djailla <https://github.com/djailla>`_.

4.1.4 (2019-09-24)
------------------

* Make tests more deterministic and easier to run outside of ``tox``.

* Fix Fedora packaging `issue <https://github.com/evansd/whitenoise/issues/225>`_.

* Use `Black <https://github.com/psf/black>`_ to format all code.

4.1.3 (2019-07-13)
------------------

* Fix handling of zero-valued mtimes which can occur when running on some filesystems (thanks `@twosigmajab <https://github.com/twosigmajab>`_ for reporting).

* Fix potential path traversal attack while running in autorefresh mode on Windows (thanks `@phith0n <https://github.com/phith0n>`_ for reporting).
  This is a good time to reiterate that autofresh mode is never intended for production use.

4.1.2 (2019-11-19)
------------------

* Add correct MIME type for WebAssembly, which is required for files to be executed (thanks `@mdboom <https://github.com/mdboom>`_ ).

* Stop accessing the ``FILE_CHARSET`` Django setting which was almost entirely unused and is now deprecated (thanks `@timgraham <https://github.com/timgraham>`_).

4.1.1 (2018-11-12)
------------------

* Fix `bug <https://github.com/evansd/whitenoise/issues/202>`_ in ETag handling (thanks `@edmorley <https://github.com/edmorley>`_).

* Documentation fixes (thanks `@jamesbeith <https://github.com/jamesbeith>`_ and `@mathieusteele <https://github.com/mathieusteele>`_).

4.1 (2018-09-12)
----------------

* Silenced spurious warning about missing directories when in development (i.e "autorefresh") mode.

* Support supplying paths as `Pathlib <https://docs.python.org/3.4/library/pathlib.html>`_ instances, rather than just strings (thanks `@browniebroke <https://github.com/browniebroke>`_).

* Add a new :ref:`CompressedStaticFilesStorage <compression-and-caching>` backend to support applying compression without applying Django's hash-versioning process.

* Documentation improvements.

4.0 (2018-08-10)
----------------

.. note:: **Breaking changes**
          The latest version of WhiteNoise removes some options which were
          deprecated in the previous major release:

* The WSGI integration option for Django
  (which involved editing ``wsgi.py``) has been removed. Instead, you
  should add WhiteNoise to your
  middleware list in ``settings.py`` and remove any reference to WhiteNoise from
  ``wsgi.py``.
  See the :ref:`documentation <django-middleware>` for more details.

  (The :doc:`pure WSGI <base>` integration is still available for non-Django apps.)

* The ``whitenoise.django.GzipManifestStaticFilesStorage`` alias has now
  been removed. Instead you should use the correct import path:
  ``whitenoise.storage.CompressedManifestStaticFilesStorage``.

If you are not using either of these integration options you should have
no issues upgrading to the latest version.

.. rubric:: Removed Python 3.3 Support

Removed support for Python 3.3 since it's end of life was in September 2017.

.. rubric:: Index file support

WhiteNoise now supports serving :ref:`index files <index-files-django>` for
directories (e.g. serving ``/example/index.html`` at ``/example/``). It also
creates redirects so that visiting the index file directly, or visiting the URL
without a trailing slash will redirect to the correct URL.

.. rubric:: Range header support ("byte serving")

WhiteNoise now respects the HTTP Range header which allows a client to request
only part of a file. The main use for this is in serving video files to iOS
devices as Safari refuses to play videos unless the server supports the
Range header.

.. rubric:: ETag support

WhiteNoise now adds ETag headers to files using the same algorithm used by
nginx. This gives slightly better caching behaviour than relying purely on Last
Modified dates (although not as good as creating immutable files using
something like ``ManifestStaticFilesStorage``, which is still the best option
if you can use it).

If you need to generate your own ETags headers for any reason you can define a
custom :any:`add_headers_function <WHITENOISE_ADD_HEADERS_FUNCTION>`.

.. rubric:: Remove requirement to run collectstatic

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

.. rubric:: Customisable immutable files test

WhiteNoise ships with code which detects when you are using Django's
ManifestStaticFilesStorage backend and sends optimal caching headers for files
which are guaranteed not to change. If you are using a different system for
generating cacheable files then you might need to supply your own function for
detecting such files. Previously this required subclassing WhiteNoise, but now
you can use the :any:`WHITENOISE_IMMUTABLE_FILE_TEST` setting.

.. rubric:: Fix runserver_nostatic to work with Channels

The old implementation of :ref:`runserver_nostatic <runserver-nostatic>` (which
disables Django's default static file handling in development) did not work
with `Channels`_, which needs its own runserver implementation. The
runserver_nostatic command has now been rewritten so that it should work with
Channels and with any other app which provides its own runserver.

.. _Channels: https://channels.readthedocs.io/

.. rubric:: Reduced storage requirements for static files

The new :any:`WHITENOISE_KEEP_ONLY_HASHED_FILES` setting reduces the number of
files in STATIC_ROOT by half by storing files only under their hashed names
(e.g.  ``app.db8f2edc0c8a.js``), rather than also keeping a copy with the
original name (e.g. ``app.js``).

.. rubric:: Improved start up performance

When in production mode (i.e. when :any:`autorefresh <WHITENOISE_AUTOREFRESH>`
is disabled), WhiteNoise scans all static files when the application starts in
order to be able to serve them as efficiently and securely as possible. For
most applications this makes no noticeable difference to start up time, however
for applications with very large numbers of static files this process can take
some time. In WhiteNoise 4.0 the file scanning code has been rewritten to do
the minimum possible amount of filesystem access which should make the start up
process considerably faster.

.. rubric:: Windows Testing

WhiteNoise has always aimed to support Windows as well as \*NIX platforms but
we are now able to run the test suite against Windows as part of the CI process
which should ensure that we can maintain Windows compatibility in future.

.. rubric:: Modification times for compressed files

The compressed storage backend (which generates Gzip and Brotli compressed
files) now ensures that compressed files have the same modification time as the
originals.  This only makes a difference if you are using the compression
backend with something other than WhiteNoise to actually serve the files, which
very few users do.

.. rubric:: Replaced brotlipy with official Brotli Python Package

Since the official `Brotli project <https://github.com/google/brotli>`_ offers
a `Brotli Python package <https://pypi.org/project/Brotli/>`_ brotlipy has been
replaced with Brotli.

Furthermore a ``brotli`` key has been added to ``extras_require`` which allows
installing WhiteNoise and Brotli together like this:

.. code-block:: bash

    pip install whitenoise[brotli]

3.3.1 (2017-09-23)
------------------

* Fix issue with the immutable file test when running behind a CDN which rewrites paths (thanks @lskillen).

3.3.0 (2017-01-26)
------------------

* Support the new `immutable <https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Cache-Control#Revalidation_and_reloading>`_ Cache-Control header.
  This gives better caching behaviour for immutable resources than simply setting a large max age.

3.2.3 (2017-01-04)
------------------

* Gracefully handle invalid byte sequences in URLs.

* Gracefully handle filenames which are too long for the filesystem.

* Send correct Content-Type for Adobe's ``crossdomain.xml`` files.

3.2.2 (2016-09-26)
------------------

* Convert any config values supplied as byte strings to text to avoid runtime encoding errors when encountering non-ASCII filenames.

3.2.1 (2016-08-09)
------------------

* Handle non-ASCII URLs correctly when using the ``wsgi.py`` integration.

* Fix exception triggered when a static files "finder" returned a directory rather than a file.

3.2 (2016-05-27)
----------------

* Add support for the new-style middleware classes introduced in Django 1.10.
  The same WhiteNoiseMiddleware class can now be used in either the old
  ``MIDDLEWARE_CLASSES`` list or the new ``MIDDLEWARE`` list.

* Fixed a bug where incorrect Content-Type headers were being sent on 304 Not
  Modified responses (thanks `@oppianmatt <https://github.com/oppianmatt>`_).

* Return Vary and Cache-Control headers on 304 responses, as specified by the
  `RFC <https://tools.ietf.org/html/rfc7232#section-4.1>`_.

3.1 (2016-05-15)
----------------

* Add new :any:`WHITENOISE_STATIC_PREFIX` setting to give flexibility in
  supporting non-standard deployment configurations e.g. serving the
  application somewhere other than the domain root.

* Fix bytes/unicode bug when running with Django 1.10 on Python 2.7

3.0 (2016-03-23)
----------------

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

.. _WhiteNoise 2.x: https://whitenoise.readthedocs.io/en/legacy-2.x/

.. rubric:: Simpler, cleaner Django middleware integration

WhiteNoise can now integrate with Django by adding a single line to
``MIDDLEWARE_CLASSES``  without any need to edit ``wsgi.py``. This also means
that WhiteNoise plays nicely with other middleware classes such as
*SecurityMiddleware*, and that it is fully compatible with the new `Channels`_
system. See the :ref:`updated documentation <django-middleware>` for details.

.. _Channels: https://channels.readthedocs.io/

.. rubric:: Brotli compression support

`Brotli`_ is the modern, more efficient alternative to gzip for HTTP
compression. To benefit from smaller files and faster page loads, just install
the `brotlipy`_ library, update your ``requirements.txt`` and WhiteNoise
will take care of the rest. See the :ref:`documentation <brotli-compression>`
for details.

.. _brotli: https://en.wikipedia.org/wiki/Brotli
.. _brotlipy: https://brotlipy.readthedocs.io/

.. rubric:: Simpler customisation

It's now possible to add custom headers to WhiteNoise without needing to create
a subclass, using the new :any:`add_headers_function
<WHITENOISE_ADD_HEADERS_FUNCTION>` setting.

.. rubric:: Use WhiteNoise in development with Django

There's now an option to force Django to use WhiteNoise in development, rather
than its own static file handling. This results in more consistent behaviour
between development and production environments and fewer opportunities for
bugs and surprises. See the :ref:`documentation <runserver-nostatic>` for
details.

.. rubric:: Improved mimetype handling

WhiteNoise now ships with its own mimetype definitions (based on those shipped
with nginx) instead of relying on the system ones, which can vary between
environments. There is a new :any:`mimetypes <WHITENOISE_MIMETYPES>`
configuration option which makes it easy to add additional type definitions if
needed.

.. rubric:: Thanks

A big thank-you to `Ed Morley <https://github.com/edmorley>`_ and `Tim Graham <https://github.com/timgraham>`_ for their contributions to this release.

2.0.6 (2015-11-15)
------------------

* Rebuild with latest version of `wheel` to get `extras_require` support.

2.0.5 (2015-11-15)
------------------

* Add missing argparse dependency for Python 2.6 (thanks @movermeyer)).

2.0.4 (2015-09-20)
------------------

* Report path on MissingFileError (thanks @ezheidtmann).

2.0.3 (2015-08-18)
------------------

* Add ``__version__`` attribute.

2.0.2 (2015-07-03)
------------------

* More helpful error message when ``STATIC_URL`` is set to the root of a domain (thanks @dominicrodger).

2.0.1 (2015-06-28)
------------------

* Add support for Python 2.6.

* Add a more helpful error message when attempting to import DjangoWhiteNoise before ``DJANGO_SETTINGS_MODULE`` is defined.

2.0 (2015-06-20)
----------------

* Add an ``autorefresh`` mode which picks up changes to static files made after application startup (for use in development).

* Add a ``use_finders`` mode for DjangoWhiteNoise which finds files in their original directories without needing them collected in ``STATIC_ROOT`` (for use in development).
  Note, this is only useful if you don't want to use Django's default runserver behaviour.

* Remove the ``follow_symlinks`` argument from ``add_files`` and now always follow symlinks.

* Support extra mimetypes which Python doesn't know about by default (including .woff2 format)

* Some internal refactoring. Note, if you subclass WhiteNoise to add custom behaviour you may need to make some small changes to your code.

1.0.6 (2014-12-12)
------------------

* Fix unhelpful exception inside `make_helpful_exception` on Python 3 (thanks @abbottc).

1.0.5 (2014-11-25)
------------------

* Fix error when attempting to gzip empty files (thanks @ryanrhee).

1.0.4 (2014-11-14)
------------------

* Don't attempt to gzip ``.woff`` files as they're already compressed.

* Base decision to gzip on compression ratio achieved, so we don't incur gzip overhead just to save a few bytes.

* More helpful error message from ``collectstatic`` if CSS files reference missing assets.

1.0.3 (2014-06-08)
------------------

* Fix bug in Last Modified date handling (thanks to Atsushi Odagiri for spotting).

1.0.2 (2014-04-29)
------------------

* Set the default max_age parameter in base class to be what the docs claimed it was.

1.0.1 (2014-04-18)
------------------

* Fix path-to-URL conversion for Windows.

* Remove cruft from packaging manifest.

1.0 (2014-04-14)
----------------

* First stable release.
