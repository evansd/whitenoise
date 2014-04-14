Infrequently Asked Questions
============================

Isn't serving static files from Python horribly inefficient? Shouldn't I be using a real webserver like nginx?
--------------------------------------------------------------------------------------------------------------

The short answer to this is that if you care about performance and efficiency
then you should be using WhiteNoise behind a CDN. And if you're doing *that*, the
vast majority of static requests will be served directly by the CDN without
touching your application, so any performance advantage something like nginx
has over WhiteNoise becomes irrelevant.

In addition, while WhiteNoise is never going to compete with nginx for raw
speed, it is pretty efficient. Because it only has to serve a fixed set of
files it does all the work of finding files and determing the correct headers
upfront on initialization. Requests can then be served with little more than a
dictionary lookup to find the appropriate response. Also, when used with
gunicorn (and most other WSGI servers) the actual business of pushing the file
down the network interface is handled by the kernel's very efficient
``sendfile`` syscall, not by Python.


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
----------------------------------------------------------------------------------

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
