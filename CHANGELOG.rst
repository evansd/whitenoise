Change Log
==========

v2.0.1
------
* Add support for Python 2.6.
* Add a more helpful error message when attempting to import DjangoWhiteNoise before `DJANGO_SETTINGS_MODULE` is defined.


v2.0
------
* Add an `autorefresh` mode which picks up changes to static files made after application startup (for use in development).
* Add a `use_finders` mode for DjangoWhiteNoise which finds files in their original directories without needing them collected in `STATIC_ROOT` (for use in development). Note, this is only useful if you don't want to use Django's default runserver behaviour.
* Remove the `follow_symlinks` argument from `add_files` and now always follow symlinks.
* Support extra mimetypes which Python doesn't know about by default (including .woff2 format)
* Some internal refactoring. Note, if you subclass WhiteNoise to add custom behaviour you may need to make some small changes to your code.


v1.0.6
------
* Fix unhelpful exception inside `make_helpful_exception` on Python 3 (thanks @abbottc).


v1.0.5
------
* Fix error when attempting to gzip empty files (thanks @ryanrhee).


v1.0.4
------
* Don't attempt to gzip ``.woff`` files as they're already compressed.
* Base decision to gzip on compression ratio achieved, so we don't incur gzip overhead just to save a few bytes.
* More helpful error message from ``collectstatic`` if CSS files reference missing assets.


v1.0.3
------
* Fix bug in Last Modified date handling (thanks to Atsushi Odagiri for spotting).


v1.0.2
------
* Set the default max_age parameter in base class to be what the docs claimed it was.


v1.0.1
------
* Fix path-to-URL conversion for Windows.
* Remove cruft from packaging manifest.


v1.0
----
* First stable release.
