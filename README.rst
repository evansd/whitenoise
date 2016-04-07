WhiteNoise
==========

.. image:: https://img.shields.io/travis/evansd/whitenoise.svg
   :target:  https://travis-ci.org/evansd/whitenoise
   :alt: Build Status

.. image:: https://img.shields.io/pypi/dm/whitenoise.svg
    :target: https://pypi.python.org/pypi/whitenoise
    :alt: Latest PyPI version

.. image:: https://img.shields.io/github/stars/evansd/whitenoise.svg?style=social&label=Star
    :target: https://github.com/evansd/whitenoise
    :alt: GitHub project

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

* Serving compressed content (gzip and Brotli formats, handling Accept-Encoding
  and Vary headers correctly)
* Setting far-future cache headers on content which won't change

Worried that serving static files with Python is horribly inefficient?
Still think you should be using Amazon S3? Have a look at the `Infrequently
Asked Questions`_.

To get started, see the documentation_.

.. _Infrequently Asked Questions: http://whitenoise.evans.io/en/stable/#infrequently-asked-questions
.. _documentation: http://whitenoise.evans.io/en/stable/
