WhiteNoise
==========

A Python library for serving static files directly from any WSGI application, with optional
easy integration with Django. It is secure and efficient enough to use in production.


Hasn't this been done already? What's new?
------------------------------------------

Yes, there's Luke Arno's Static_ and Kenneth Reitz's dj-static_ which is built on top of it.
However WhiteNoise offers a few benefits:

 * Python 2/3 compatibility
 * Serves pre-gzipped content (handling Accept-Encoding and Vary headers correctly)
 * Customisable HTTP headers, in particular:

   - Cache headers (crucial if you're serving files to a CDN)
   - Allow-Origin headers (crucial if you're serving font files to applications on a different domain)

 * Can serve static files from arbitrary URLs, not just from a fixed URL prefix, so
   you can use it to serve files like ``/favicon.ico`` or ``/robots.txt``

.. _dj-static: https://github.com/kennethreitz/dj-static
.. _Static: http://lukearno.com/projects/static/


Tell me more
------------
Read the documentation: http://whitenoise.evans.io
