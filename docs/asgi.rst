Using WhiteNoise with any ASGI application
==========================================

.. note:: These instructions apply to any ASGI application. However, for Django
    applications you would be better off using the :doc:`WhiteNoiseMiddleware
    <django>` class which makes integration easier.

To enable WhiteNoise you need to wrap your existing ASGI application in a
WhiteNoise instance and tell it where to find your static files. For example:

.. code-block:: python

   from whitenoise import AsgiWhiteNoise

   from my_project import MyASGIApp

   application = MyWAGIApp()
   application = AsgiWhiteNoise(application, root="/path/to/static/files")
   application.add_files("/path/to/more/static/files", prefix="more-files/")

On initialization, WhiteNoise walks over all the files in the directories that have
been added (descending into sub-directories) and builds a list of available static files.
Any requests which match a static file get served by WhiteNoise, all others are passed
through to the original WSGI application.


.. tip:: ``AsgiWhiteNoise`` inherits all interfaces from WSGI ``WhiteNoise`` but adds
    support for ASGI applications. See the :doc:`WSGI WhiteNoise documentation <wsgi>` for
    more details.


AsgiWhiteNoise API
------------------

``AsgiWhiteNoise`` inherits its interface from WSGI ``WhiteNoise``, however, ``application``
must be an ASGI application.

See the section on WSGI ``WhiteNoise`` :ref:`interface <interface>` for details.


Compression Support
--------------------

See the section on WSGI ``WhiteNoise`` :ref:`compression support <compression>` for details.


Caching Headers
---------------

See the section on WSGI ``WhiteNoise`` :ref:`caching headers <caching>` for details.


Index Files
-----------

See the section on WSGI ``WhiteNoise`` :ref:`index files <index_files>` for details.


Using a Content Distribution Network
------------------------------------

See the instructions for :ref:`using a CDN with Django <cdn>` . The same principles
apply here although obviously the exact method for generating the URLs for your static
files will depend on the libraries you're using.


Redirecting to HTTPS
--------------------

See the section on WSGI ``WhiteNoise`` :ref:`redirecting to HTTPS <https>` for details.


Configuration attributes
------------------------

See the section on WSGI ``WhiteNoise`` :ref:`configuration attributes <configuration>` for details.
