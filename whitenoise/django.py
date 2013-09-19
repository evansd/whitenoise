from __future__ import absolute_import

import os.path

try:
    import urlparse
except ImportError:
    import urllib.parse as urlparse

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.contrib.staticfiles.storage import staticfiles_storage

from .base import WhiteNoise


class DjangoWhiteNoise(WhiteNoise):

    # Ten years is what nginx sets a max age if you use 'expires max;'
    # so we'll follow its lead
    FOREVER = 10*365*24*60*60

    # Cache expiry time for non-versioned files
    max_age = 60
    root = None

    def __init__(self, application):
        # Allow settings to override default attributes
        for attr in ('root', 'gzip_enabled', 'max_age', 'static_max_age'):
            settings_key = 'WHITENOISE_{}'.format(attr.upper())
            try:
                setattr(self, attr, getattr(settings, settings_key))
            except AttributeError:
                pass
        static_root, static_prefix = self.get_static_root_and_prefix()
        self.static_prefix = static_prefix
        super(DjangoWhiteNoise, self).__init__(application, root=self.root)
        self.add_files(static_root, prefix=static_prefix)

    def get_static_root_and_prefix(self):
        static_url = getattr(settings, 'STATIC_URL', None)
        static_root = getattr(settings, 'STATIC_ROOT', None)
        if not static_url or not static_root:
            raise ImproperlyConfigured('Both STATIC_URL and STATIC_ROOT '
                    'settings must be configured to use DjangoWhiteNoise')
        static_prefix = urlparse.urlparse(static_url).path
        static_prefix = '/{}/'.format(static_prefix.strip('/'))
        return static_root, static_prefix

    def add_extra_headers(self, static_file, url):
        # Versioned files can be safely cached forever
        if self.is_versioned_file(url):
            static_file.headers['Cache-Control'] = 'public, max-age={}'.format(self.FOREVER)

    def is_versioned_file(self, url):
        """
        Determine whether given URL represents a versioned file (i.e. a
        file with a hash of its contents as part of its name)
        """
        if not url.startswith(self.static_prefix):
            return False
        name = url[len(self.static_prefix):]
        name_without_hash = self.get_name_without_hash(name)
        if name == name_without_hash:
            return False
        static_url = self.get_static_url(name_without_hash)
        # If the static URL function maps the name without hash
        # back to the original URL, then we know we've got a
        # versioned filename
        if static_url and static_url.endswith(url):
            return True
        return False

    def get_name_without_hash(self, filename):
        """
        Removes the version hash from a filename e.g, transforms
        'css/application.f3ea4bcc2.css' into 'css/application.css'

        Note: this is specific to the naming scheme used by Django's
        CachedStaticFilesStorage. You may have to override this if
        you are using a different static files versioning system
        """
        name_with_hash, ext = os.path.splitext(filename)
        name = os.path.splitext(name_with_hash)[0]
        return name + ext

    def get_static_url(self, name):
        try:
            return staticfiles_storage.url(name)
        except ValueError:
            return None
