<!--desc-start-->

# ServeStatic

<!-- TODO: Fix these links -->
<p>
    <a href="https://github.com/Archmonger/ServeStatic/actions?query=workflow%3ATest">
        <img src="https://github.com/Archmonger/ServeStatic/workflows/Test/badge.svg?event=push">
    </a>
    <a href="https://pypi.python.org/pypi/servestatic">
        <img src="https://img.shields.io/pypi/v/servestatic.svg?label=PyPI">
    </a>
    <a href="https://github.com/Archmonger/ServeStatic/blob/main/LICENSE.md">
        <img src="https://img.shields.io/badge/License-MIT-purple.svg">
    </a>
    <a href="https://archmonger.github.io/ServeStatic/">
        <img src="https://img.shields.io/website?down_message=offline&label=Docs&logo=read%20the%20docs&logoColor=white&up_message=online&url=https%3A%2F%2Farchmonger.github.io%2Fservestatic%2F">
    </a>
</p>

_Simplified static file serving for Python web apps._

---

With a couple of lines of configuration `ServeStatic` allows your web app to serve its own static files, making it a self-contained unit that can be deployed anywhere without relying on nginx, Amazon S3, or any other external service. This is especially useful on Heroku, OpenShift, and other PaaS providers.

It's designed to work nicely with a CDN for high-traffic sites so you don't have to sacrifice performance to benefit from simplicity.

`ServeStatic` works with any ASGI or WSGI compatible app but has some special auto-configuration features for Django.

`ServeStatic` automatically takes care of best-practices for you, for instance:

- Serving compressed content (gzip and Brotli formats, handling Accept-Encoding and Vary headers correctly)
- Setting far-future cache headers on content which won't change

Worried that serving static files with Python is horribly inefficient? Still think you should be using Amazon S3? Have a look at the FAQ below.

## Frequently Asked Questions

### Isn't serving static files from Python horribly inefficient?

The short answer to this is that if you care about performance and efficiency then you should be using `ServeStatic` behind a CDN like CloudFront. If you're doing _that_ then, because of the caching headers `ServeStatic` sends, the vast majority of static requests will be served directly by the CDN without touching your application, so it really doesn't make much difference how efficient `ServeStatic` is.

That said, `ServeStatic` is pretty efficient. Because it only has to serve a fixed set of files it does all the work of finding files and determining the correct headers upfront on initialization. Requests can then be served with little more than a dictionary lookup to find the appropriate response. Also, when used with gunicorn (and most other WSGI servers) the actual business of pushing the file down the network interface is handled by the kernel's very efficient `sendfile` syscall, not by Python.

### Shouldn't I be pushing my static files to S3 using something like Django-Storages?

No, you shouldn't. The main problem with this approach is that Amazon S3 cannot currently selectively serve compressed content to your users. Compression (using either the venerable gzip or the more modern brotli algorithms) can make dramatic reductions in the bandwidth required for your CSS and JavaScript. But in order to do this correctly the server needs to examine the `Accept-Encoding` header of the request to determine which compression formats are supported, and return an appropriate `Vary` header so that intermediate caches know to do the same. This is exactly what `ServeStatic` does, but Amazon S3 currently provides no means of doing this.

The second problem with a push-based approach to handling static files is that it adds complexity and fragility to your deployment process: extra libraries specific to your storage backend, extra configuration and authentication keys, and extra tasks that must be run at specific points in the deployment in order for everything to work. With the CDN-as-caching-proxy approach that `ServeStatic` takes there are just two bits of configuration: your application needs the URL of the CDN, and the CDN needs the URL of your application. Everything else is just standard HTTP semantics. This makes your deployments simpler, your life easier, and you happier.

### What's the point in `ServeStatic` when I can do the same thing in a few lines of `apache`/`nginx`?

There are two answers here. One is that ServeStatic is designed to work in situations where `apache`, `nginx`, and the like aren't easily available. But more importantly, it's easy to underestimate what's involved in serving static files correctly. Does your few lines of nginx configuration distinguish between files which might change and files which will never change and set the cache headers appropriately? Did you add the right CORS headers so that your fonts load correctly when served via a CDN? Did you turn on the special nginx setting which allows it to send gzip content in response to an `HTTP/1.0` request, which for some reason CloudFront still uses? Did you install the extension which allows you to serve brotli-encoded content to modern browsers?

None of this is rocket science, but it's fiddly and annoying and `ServeStatic` takes care of all it for you.

<!--desc-end-->

---

_This project is a fork of [WhiteNoise](https://github.com/evansd/whitenoise) for continued maintenience and feature updates._
