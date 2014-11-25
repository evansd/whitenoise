Change Log
==========

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
