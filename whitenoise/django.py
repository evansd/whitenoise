from __future__ import absolute_import

try:
    import urlparse
except ImportError:
    import urllib.parse as urlparse

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.contrib.staticfiles.storage import staticfiles_storage, CachedFilesMixin

from .base import WhiteNoise


class DjangoWhiteNoise(WhiteNoise):

    # Cache expiry time for any files which aren't in STATIC_ROOT
    default_max_age = 60

    # Cache expiry time for files in STATIC_ROOT. Default of None
    # means that this value is automatically determined based on
    # whether or not you're using CachedFilesMixin
    static_max_age = None

    def __init__(self, application):
        # Allow settings to override default attributes
        for attr in ('gzip_enabled', 'default_max_age', 'static_max_age'):
            settings_key = 'WHITENOISE_{}'.format(attr.upper())
            try:
                setattr(self, attr, getattr(settings, settings_key))
            except AttributeError:
                pass
        static_root, static_prefix = self.get_static_root_and_prefix()
        self.static_prefix = static_prefix
        if self.static_max_age is None:
            self.static_max_age = self.guess_static_max_age()
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

    def guess_static_max_age(self):
        # If you're using the CachedFilesMixin, which creates unique names
        # for each file, then we assume it's safe to cache these files
        # for a long time
        # Do this dance to get the actual Storage instance rather than
        # the LazyObject wrapper
        storage_instance = staticfiles_storage.url.__self__
        if isinstance(storage_instance, CachedFilesMixin):
            # 10 years is what nginx does if you say 'expire max' so we
            # just copy that
            return 10*365*24*60*60
        else:
            return self.default_max_age

    def add_extra_headers(self, static_file, url):
        if url.startswith(self.static_prefix) and self.static_max_age is not None:
            cache_control = 'public, max-age={}'.format(self.static_max_age)
            static_file.headers['Cache-Control'] = cache_control
