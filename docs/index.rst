WhiteNoise
==========

.. image:: https://travis-ci.org/evansd/whitenoise.png
   :target:  https://travis-ci.org/evansd/whitenoise
   :alt: Build Status

.. image:: https://badge.fury.io/py/whitenoise.png
    :target: https://pypi.python.org/pypi/whitenoise
    :alt: Latest PyPI version

**Radically simplified static file serving for Python web apps**

With a couple of lines of config WhiteNoise allows your web app to serve its
own static files, making it a self-contained unit that can be deployed anywhere
without relying on nginx, Amazon S3 or any other external service. (Especially
useful on Heroku, OpenShift and other PaaS providers.)

It's designed to work nicely with a CDN for high-traffic sites so you don't have to
sacrifice performance to benefit from simplicity.

WhiteNoise works with any WSGI-compatible app but has some special auto-configuration
features for Django.

WhiteNoise takes care of best-practices for you, for instance:

* Serving gzipped content (handling Accept-Encoding and Vary headers correctly)
* Setting far-future cache headers on content which won't change

Worried that serving static files with Python is horribly inefficient?
Still think you should be using Amazon S3? Have a look at the `Infrequently
Asked Questions`_ below.


QuickStart for Django apps
--------------------------

Edit your ``wsgi.py`` file and wrap your WSGI application like so:

.. code-block:: python

   from django.core.wsgi import get_wsgi_application
   from whitenoise.django import DjangoWhiteNoise

   application = get_wsgi_application()
   application = DjangoWhiteNoise(application)

That's it, you're ready to go.

Want forever-cachable files and gzip support? Just add this to your ``settings.py``:

.. code-block:: python

   STATICFILES_STORAGE = 'whitenoise.django.GzipManifestStaticFilesStorage'

For more details, including on setting up
CloudFront and other CDNs see the :doc:`Using WhiteNoise with Django <django>`
guide.


QuickStart for other WSGI apps
------------------------------

To enable WhiteNoise you need to wrap your existing WSGI application in a
WhiteNoise instance and tell it where to find your static files. For example:

.. code-block:: python

   from whitenoise import WhiteNoise

   from my_project import MyWSGIApp

   application = MyWSGIApp()
   application = WhiteNoise(application, root='/path/to/static/files')
   application.add_files('/path/to/more/static/files', prefix='more-files/')

And that's it, you're ready to go. For more details see the :doc:`full
documentation <base>`.


Compatibility
-------------

WhiteNoise works with any WSGI-compatible application and is tested on Python **2.7**, **3.3** and **3.4**

DjangoWhiteNoise is tested with Django versions **1.4** --- **1.8**


Endorsements
------------

WhiteNoise is being used in `Warehouse <https://github.com/pypa/warehouse>`_, the in-development
replacement for the PyPI package repository.

Some of Django and pip's core developers have said nice things about it:

   `@jezdez <https://twitter.com/jezdez/status/440901769821179904>`_: *[WhiteNoise]
   is really awesome and should be the standard for Django + Heroku*

   `@dstufft <https://twitter.com/dstufft/status/440948000782032897>`_: *WhiteNoise
   looks pretty excellent.*

   `@idangazit <https://twitter.com/idangazit/status/456720556331528192>`_ *Received
   a positive brainsmack from @_EvansD's WhiteNoise. Vastly smarter than S3 for
   static assets. What was I thinking before?*


Issues & Contributing
---------------------

Raise an issue on the `GitHub project <https://github.com/evansd/whitenoise>`_ or
feel free to nudge `@_EvansD <https://twitter.com/_evansd>`_ on Twitter.


Infrequently Asked Questions
----------------------------


Isn't serving static files from Python horribly inefficient?
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

The short answer to this is that if you care about performance and efficiency
then you should be using WhiteNoise behind a CDN like CloudFront. If you're
doing *that* then, because of the caching headers WhiteNoise sends, the vast
majority of static requests will be served directly by the CDN without touching
your application, so it really doesn't make much difference how efficient
WhiteNoise is.

That said, WhiteNoise is pretty efficient. Because it only has to serve a fixed set of
files it does all the work of finding files and determing the correct headers
upfront on initialization. Requests can then be served with little more than a
dictionary lookup to find the appropriate response. Also, when used with
gunicorn (and most other WSGI servers) the actual business of pushing the file
down the network interface is handled by the kernel's very efficient
``sendfile`` syscall, not by Python.


Shouldn't I be pushing my static files to S3 using something like Django-Storages?
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

No, you shouldn't. The main problem with this approach is that Amazon S3 cannot
currently selectively serve gzipped content to your users. Gzipping can make
dramatic reductions in the bandwidth required for your CSS and JavaScript. But
while all browsers in use today can decode gzipped content, your users may be
behind crappy corporate proxies or anti-virus scanners which don't handle
gzipped content properly. Amazon S3 forces you to choose whether to serve
gzipped content to no-one (wasting bandwidth) or everyone (running the risk of
your site breaking for certain users).

The correct behaviour is to examine the ``Accept-Encoding`` header of the
request to see if gzip is supported, and to return an appropriate ``Vary``
header so that intermediate caches know to do the same thing. This is exactly
what WhiteNoise does.

The second problem with a push-based approach to handling static files is that
it adds complexity and fragility to your deployment process: extra libraries
specific to your storage backend, extra configuration and authentication keys,
and extra tasks that must be run at specific points in the deployment in order
for everythig to work.  With the CDN-as-caching-proxy approach that WhiteNoise
takes there are just two bits of configuration: your application needs the URL
of the CDN, and the CDN needs the URL of your application. Everything else is
just standard HTTP semantics. This makes your deployments simpler, your life
easier, and you happier.


License
-------

MIT Licensed

.. toctree::
   :hidden:

   self
   django
   base
   changelog
