from __future__ import absolute_import

import os.path

try:
    import urlparse
except ImportError:
    import urllib.parse as urlparse

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.contrib.staticfiles.storage import staticfiles_storage
try:
    from django.contrib.staticfiles.storage import ManifestStaticFilesStorage
except ImportError:
    # For Django versions < 1.7
    from .storage_backport import ManifestStaticFilesStorage

from .base import WhiteNoise
from .gzip import compress, extension_regex, GZIP_EXCLUDE_EXTENSIONS


class DjangoWhiteNoise(WhiteNoise):

    # Cache expiry time for non-versioned files
    max_age = 60

    def __init__(self, application):
        self.charset = settings.FILE_CHARSET
        # Allow settings to override default attributes
        for attr in self.config_attrs:
            settings_key = 'WHITENOISE_{}'.format(attr.upper())
            try:
                setattr(self, attr, getattr(settings, settings_key))
            except AttributeError:
                pass
        static_root, static_prefix = self.get_static_root_and_prefix()
        self.static_prefix = static_prefix
        root = getattr(settings, 'WHITENOISE_ROOT', None)
        super(DjangoWhiteNoise, self).__init__(application, root=root)
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

    def is_immutable_file(self, static_file, url):
        """
        Determine whether given URL represents an immutable file (i.e. a
        file with a hash of its contents as part of its name) which can
        therefore be cached forever
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


class GzipStaticFilesMixin(object):

    CHUNK_SIZE = 64 * 1024

    def post_process(self, *args, **kwargs):
        files = super(GzipStaticFilesMixin, self).post_process(*args, **kwargs)
        dry_run = kwargs.get('dry_run', False)
        extensions = getattr(settings, 'WHITENOISE_GZIP_EXCLUDE_EXTENSIONS',
                GZIP_EXCLUDE_EXTENSIONS)
        excluded_re = extension_regex(extensions)
        for name, hashed_name, processed in files:
            if not dry_run and not excluded_re.search(name):
                compress(self.path(name))
                if hashed_name is not None:
                    compress(self.path(hashed_name))
            yield name, hashed_name, processed


class GzipManifestStaticFilesStorage(GzipStaticFilesMixin, ManifestStaticFilesStorage):
    pass
