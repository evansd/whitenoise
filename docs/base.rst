Using WhiteNoise with any WSGI application
==========================================

.. note:: These instructions apply to any WSGI application. However, for Django
    applications you would be better off using the :doc:`WhiteNoiseMiddleware
    <django>` class which makes integration easier.

To enable WhiteNoise you need to wrap your existing WSGI application in a
WhiteNoise instance and tell it where to find your static files. For example:

.. code-block:: python

   from whitenoise import WhiteNoise

   from my_project import MyWSGIApp

   application = MyWSGIApp()
   application = WhiteNoise(application, root="/path/to/static/files")
   application.add_files("/path/to/more/static/files", prefix="more-files/")

On initialization, WhiteNoise walks over all the files in the directories that have
been added (descending into sub-directories) and builds a list of available static files.
Any requests which match a static file get served by WhiteNoise, all others are passed
through to the original WSGI application.

See the sections on :ref:`compression <compression>` and :ref:`caching <caching>`
for further details.


WhiteNoise API
--------------

.. class:: WhiteNoise(application, root=None, prefix=None, \**kwargs)

   :param callable application: Original WSGI application
   :param str root: If set, passed to ``add_files`` method
   :param str prefix: If set, passed to ``add_files`` method
   :param  \**kwargs: Sets :ref:`configuration attributes <configuration>` for this instance

.. method:: WhiteNoise.add_files(root, prefix=None)

   :param str root: Absolute path to a directory of static files to be served
   :param str prefix: If set, the URL prefix under which the files will be served. Trailing slashes
    are automatically added.


.. _compression:

Compression Support
-------------------

When WhiteNoise builds its list of available files it checks for corresponding
files with a ``.gz`` and a ``.br`` suffix (e.g., ``scripts/app.js``,
``scripts/app.js.gz`` and ``scripts/app.js.br``). If it finds them, it will
assume that they are (respectively) gzip and `brotli <https://en.wikipedia.org/wiki/Brotli>`_
compressed versions of the original file and it will serve them in preference
to the uncompressed version where clients indicate that they that compression
format (see note on Amazon S3 for why this behaviour is important).

.. _cli-utility:

WhiteNoise comes with a command line utility which will generate compressed
versions of your files for you. Note that in order for brotli compression to
work the `Brotli Python package <https://pypi.org/project/Brotli/>`_ must be installed.


Usage is simple:

.. code-block:: console

   $ python -m whitenoise.compress --help
   usage: compress.py [-h] [-q] [--no-gzip] [--no-brotli]
                      root [extensions [extensions ...]]

   Search for all files inside <root> *not* matching <extensions> and produce
   compressed versions with '.gz' and '.br' suffixes (as long as this results in
   a smaller file)

   positional arguments:
     root         Path root from which to search for files
     extensions   File extensions to exclude from compression (default: jpg,
                  jpeg, png, gif, webp, zip, gz, tgz, bz2, tbz, xz, br, swf, flv,
                  woff, woff2)

   optional arguments:
     -h, --help   show this help message and exit
     -q, --quiet  Don't produce log output
     --no-gzip    Don't produce gzip '.gz' files
     --no-brotli  Don't produce brotli '.br' files

You can either run this during development and commit your compressed files to
your repository, or you can run this as part of your build and deploy processes.
(Note that this is handled automatically in Django if you're using the custom
storage backend.)


.. _caching:

Caching Headers
---------------

By default, WhiteNoise sets a max-age header on all responses it sends. You can
configure this by passing a ``max_age`` keyword argument.

WhiteNoise sets both ``Last-Modified`` and ``ETag`` headers for all files and
will return Not Modified responses where appropriate. The ETag header uses the
same format as nginx which is based on the size and last-modified time of the file.
If you want to use a different scheme for generating ETags you can set them via
you own function by using the :any:`add_headers_function` option.

Most modern static asset build systems create uniquely named versions of each
file. This results in files which are immutable (i.e., they can never change
their contents) and can therefore by cached indefinitely.  In order to take
advantage of this, WhiteNoise needs to know which files are immutable. This can
be done using the :any:`immutable_file_test` option which accepts a reference to
a function.

The exact details of how you implement this method will depend on your
particular asset build system but see the :any:`option documentation
<immutable_file_test>` for a simple example.

Once you have implemented this, any files which are flagged as immutable will
have "cache forever" headers set.


.. _index_files:

Index Files
-----------

When the :any:`index_file` option is enabled:

* Visiting ``/example/`` will serve the file at ``/example/index.html``
* Visiting ``/example`` will redirect (302) to ``/example/``
* Visiting ``/example/index.html`` will redirect (302) to ``/example/``

If you want to something other than ``index.html`` as the index file, then you
can also set this option to an alternative filename.


Using a Content Distribution Network
------------------------------------

See the instructions for :ref:`using a CDN with Django <cdn>` . The same principles
apply here although obviously the exact method for generating the URLs for your static
files will depend on the libraries you're using.


Redirecting to HTTPS
--------------------

WhiteNoise does not handle redirection itself, but works well alongside
`wsgi-sslify`_, which performs HTTP to HTTPS redirection as well as optionally
setting an HSTS header. Simply wrap the WhiteNoise WSGI application with
``sslify()`` - see the `wsgi-sslify`_ documentation for more details.

.. _wsgi-sslify: https://github.com/jacobian/wsgi-sslify


.. _configuration:

Configuration attributes
------------------------

These can be set by passing keyword arguments to the constructor, or by
sub-classing WhiteNoise and setting the attributes directly.

.. attribute:: autorefresh

    :default: ``False``

    Recheck the filesystem to see if any files have changed before responding.
    This is designed to be used in development where it can be convenient to
    pick up changes to static files without restarting the server. For both
    performance and security reasons, this setting should not be used in
    production.

.. attribute:: max_age

    :default: ``60``

    Time (in seconds) for which browsers and proxies should cache files.

    The default is chosen to be short enough not to cause problems with stale versions but
    long enough that, if you're running WhiteNoise behind a CDN, the CDN will still take
    the majority of the strain during times of heavy load.


.. attribute:: index_file

    :default: ``False``

    If ``True`` enable :ref:`index file serving <index_files>`. If set to a non-empty
    string, enable index files and use that string as the index file name.


.. attribute:: mimetypes

    :default: ``None``

    A dictionary mapping file extensions (lowercase) to the mimetype for that
    extension. For example: ::

        {'.foo': 'application/x-foo'}

    Note that WhiteNoise ships with its own default set of mimetypes and does
    not use the system-supplied ones (e.g. ``/etc/mime.types``). This ensures
    that it behaves consistently regardless of the environment in which it's
    run.  View the defaults in the :file:`media_types.py
    <whitenoise/media_types.py>` file.

    In addition to file extensions, mimetypes can be specified by supplying the entire
    filename, for example: ::

        {'some-special-file': 'application/x-custom-type'}

.. attribute:: charset

    :default: ``utf-8``

    Charset to add as part of the ``Content-Type`` header for all files whose
    mimetype allows a charset.

.. attribute:: allow_all_origins

    :default: ``True``

    Toggles whether to send an ``Access-Control-Allow-Origin: *`` header for all
    static files.

    This allows cross-origin requests for static files which means your static files
    will continue to work as expected even if they are served via a CDN and therefore
    on a different domain. Without this your static files will *mostly* work, but you
    may have problems with fonts loading in Firefox, or accessing images in canvas
    elements, or other mysterious things.

    The W3C `explicitly state`__ that this behaviour is safe for publicly
    accessible files.

.. __: https://www.w3.org/TR/cors/#security

.. attribute:: add_headers_function

    :default: ``None``

    Reference to a function which is passed the headers object for each static file,
    allowing it to modify them.

    For example: ::

        def force_download_pdfs(headers, path, url):
            if path.endswith('.pdf'):
                headers['Content-Disposition'] = 'attachment'

        application = WhiteNoise(application,
                                 add_headers_function=force_download_pdfs)

    The function is passed:

    headers
      A `wsgiref.headers`__ instance (which you can treat just as a dict) containing
      the headers for the current file

    path
      The absolute path to the local file

    url
      The host-relative URL of the file e.g. ``/static/styles/app.css``

    The function should not return anything; changes should be made by modifying the
    headers dictionary directly.

.. __: https://docs.python.org/3/library/wsgiref.html#module-wsgiref.headers


.. attribute:: immutable_file_test

    :default: ``return False``

    Reference to function, or string.

    If a reference to a function, this is passed the path and URL for each
    static file and should return whether that file is immutable, i.e.
    guaranteed not to change, and so can be safely cached forever.

    If a string, this is treated as a regular expression and each file's URL is
    matched against it.

    Example: ::

        def immutable_file_test(path, url):
            # Match filename with 12 hex digits before the extension
            # e.g. app.db8f2edc0c8a.js
            return re.match(r'^.+\.[0-9a-f]{12}\..+$', url)

    The function is passed:

    path
      The absolute path to the local file

    url
      The host-relative URL of the file e.g. ``/static/styles/app.css``
