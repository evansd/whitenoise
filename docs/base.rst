Using WhiteNoise with any WSGI application
==========================================

.. note:: These instructions apply to any WSGI application. However, for Django
    applications you would be better off using the :doc:`DjangoWhiteNoise <django>`
    class which makes integration easier.

To enable WhiteNoise you need to wrap your existing WSGI application in a
WhiteNoise instance and tell it where to find your static files. For example:

.. code-block:: python

   from whitenoise import WhiteNoise

   from my_project import MyWSGIApp

   application = MyWSGIApp()
   application = WhiteNoise(application, root='/path/to/static/files')
   application.add_files('/path/to/more/static/files', prefix='more-files/')

On initialization, WhiteNoise walks over all the files in the directories that have
been added (descending into sub-directories) and builds a list of available static files.
Any requests which match a static file get served by WhiteNoise, all others are passed
through to the original WSGI application.

See the sections on :ref:`gzip handling <gzip>` and :ref:`caching <caching>`
for further details.


WhiteNoise API
--------------

.. class:: WhiteNoise(application, root=None, prefix=None, \**kwargs)

   :param callable application: Original WSGI application
   :param str root: If set, passed to ``add_files`` method
   :param str prefix: If set, passed to ``add_files`` method
   :param  \**kwargs: Sets :ref:`configuration attributes <configuration>` for this instance

.. method:: WhiteNoise.add_files(root, prefix=None, followlinks=False)

   :param str root: Absolute path to a directory of static files to be served
   :param str prefix: If set, the URL prefix under which the files will be served. Trailing slashes
    are automatically added.
   :param bool followlinks: Whether to follow directory symlinks when walking the directory tree to find files. Note that
    symlinks to files will always work.


.. _gzip:

Gzip Support
------------

When WhiteNoise builds its list of available files it checks for a
corresponding file with a ``.gz`` suffix (e.g., ``scripts/app.js`` and
``scripts/app.js.gz``). If it finds one, it will assume that this is a
gzip-compressed version of the original file and it will serve this in
preference to the uncompressed version where clients indicate that they accept
gzipped content (see note on Amazon S3 for why this behavour is important).

WhiteNoise comes with a command line utility which will generate gzipped versions of your
files for you. Usage is simple:

.. code-block:: console

    $ python -m whitenoise.gzip --help

    usage: gzip.py [-h] [-q] root [extensions [extensions ...]]

    Search for all files inside <root> *not* matching <extensions> and produce
    gzipped versions with a '.gz' suffix (as long this results in a smaller file)

    positional arguments:
      root         Path root from which to search for files
      extensions   File extensions to exclude from gzipping (default: jpg, jpeg,
                   png, gif, zip, gz, tgz, bz2, tbz, swf, flv, woff)

    optional arguments:
      -h, --help   show this help message and exit
      -q, --quiet  Don't produce log output (default: False)

You can either run this during development and commit your compressed files to
your repository, or you can run this as part of your build and deploy processs.
(Note that DjangoWhiteNoise handles this automatically, if you're using the
custom storage backend.)


.. _caching:

Caching Headers
---------------

By default, WhiteNoise sets a max-age header on all responses it sends. You can
configure this by passing a ``max_age`` keyword argument.

Most modern static asset build systems create uniquely named versions of each
file. This results in files which are immutable (i.e., they can never change
their contents) and can therefore by cached indefinitely.  In order to take
advantage of this, WhiteNoise needs to know which files are immutable. This can
be done by sub-classing WhiteNoise and overriding the following method:

.. code-block:: python

   def is_immutable_file(self, static_file, url):
      return False

The exact details of how you implement this method will depend on your particular asset
build system (see the source for DjangoWhiteNoise for inspiration).

Once you have implemented this, any files which are flagged as immutable will have 'cache
forever' headers set.


Using a Content Distribution Network
------------------------------------

See the instructions for :ref:`using a CDN with Django <cdn>` . The same principles
apply here although obviously the exact method for generating the URLs for your static
files will depend on the libraries you're using.


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

    The W3C `explicity state`__ that this behaviour is safe for publicly
    accessible files.

.. __: http://www.w3.org/TR/cors/#security
