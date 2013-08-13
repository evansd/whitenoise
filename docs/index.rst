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


Shouldn't I be using a real webserver?
--------------------------------------

Well, perhaps. Certainly something like nginx will be more efficient at serving static
files. But here are a few things to consider:

1. There are situations (e.g., when hosted on Heroku) where it's much simpler to have
   everything handled by your Python application.

2. WhiteNoise is pretty efficient itself. As it only has to serve a limited, fixed set of
   files it does as much work as it can upfront on itialization so it can serve responses
   with very little work. Also, when used with gunicorn (and most other WSGI servers) the
   actual business of pushing the file down the network interface is handled by the OS's
   highly efficient ``sendfile`` implementation, not by Python.

3. If you're using WhiteNoise as the upstream to a CDN (on which more below) then it
   doesn't really matter that it's not as efficient as nginx as the vast majority of
   static requests will be cached by the CDN and never touch your application.


Shouldn't I be using a CDN?
---------------------------

Yes, given how cheap and straightforward they are these days, you probably should.
But you should be using WhiteNoise to act as the origin, or upstream, server to
your CDN.

Under this model, the CDN acts as a caching proxy which sits between your application
and the browser (only for static files, you still use your normal domain for dynamic
requests). WhiteNoise will send the appropriate cache headers so the CDN can serve
requests for static files without hitting your application.


Shouldn't I be pushing my static files to S3 using something like Django-Storages?
-----------------------------------------------------------------------------------------------

No, you shouldn't. The problem with this is that Amazon S3 cannot currently selectively serve
gzipped content to your users. Gzipping can make dramatic reductions in the bandwidth required
for your CSS and JavaScript. But while all browsers in use today can decode gzipped content, your
users may be behind crappy corporate proxies or anti-virus scanners which don't handle gzipped
content properly. Amazon S3 forces you to choose whether to serve gzipped content to no-one
(wasting bandwidth) or everyone (running the risk of your site breaking for certain users).

The correct behaviour is to examine the ``Accept-Encoding`` header of the request to see if gzip
is supported, and to return an appropriate ``Vary`` header so that intermediate caches know to do
the same thing. This is exactly what WhiteNoise does.

Contents
--------

.. toctree::
   :maxdepth: 2
