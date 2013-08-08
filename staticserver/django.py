from __future__ import absolute_import, unicode_literals

try:
    import urlparse
except ImportError:
    import urllib.parse as urlparse

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.contrib.staticfiles.storage import get_storage_class, CachedFilesMixin

from .base import StaticServer


class DjangoStaticServer(StaticServer):

    # Cache expiry time for any files which aren't in STATIC_ROOT
    default_max_age = 60
    # Cache expiry time for files in STATIC_ROOT. Default of None
    # means that this value is automatically determined based on
    # whether or not you're using CachedFilesMixin
    static_max_age = None

    def __init__(self, application):
        static_prefix = urlparse.urlparse(settings.STATIC_URL).path
        static_prefix = '/{}/'.format(static_prefix.strip('/'))
        self.static_prefix = static_prefix
        # If a root dir is specified use it, but check that STATIC_ROOT
        # and STATIC_URL are appropriately configured
        if getattr(settings, 'STATICSERVER_ROOT', None):
            root = settings.STATICSERVER_ROOT
            prefix = None
            self.check_settings(root, settings.STATIC_ROOT, static_prefix)
        # If no root dir is specified, just serve the files in STATIC_ROOT
        else:
            root = settings.STATIC_ROOT
            prefix = static_prefix
        # Allow settings to override default attributes
        for attr in ('default_max_age', 'static_max_age'):
            settings_key = 'STATICSERVER_{}'.format(attr.upper())
            try:
                setattr(self, attr, getattr(settings, settings_key))
            except AttributeError:
                pass
        if self.static_max_age is None:
            self.static_max_age = self.guess_static_max_age()
        super(DjangoStaticServer, self).__init__(application, root, prefix=prefix)

    def check_settings(self, root, static_root, static_prefix):
        # This is where static files will in fact be served from, given the
        # root path and the STATIC_URL prefix
        de_facto_static_root = root.rstrip('/') + static_prefix.rstrip('/')
        # This is where Django thinks your static files live
        static_root = static_root.rstrip('/')
        # Check they're the same
        if static_root != de_facto_static_root:
            raise ImproperlyConfigured("You need to adjust your STATIC_ROOT "
                    "setting to point to '{}'".format(de_facto_static_root))

    def guess_static_max_age(self):
        # If you're using the CachedFilesMixin, which creates unique names
        # for each file, then we assume it's safe to cache these files
        # for a long time
        storage_class = get_storage_class(settings.STATICFILES_STORAGE)
        if issubclass(storage_class, CachedFilesMixin):
            # 10 years is what nginx does if you say 'expire max' so we
            # just copy that
            return 10*365*24*60*60
        else:
            return self.default_max_age

    def add_extra_headers(self, headers, file_path, url):
        if url.startswith(self.static_prefix):
            max_age = self.static_max_age
        else:
            max_age = self.default_max_age
        headers['Cache-Control'] = 'max-age={}'.format(max_age)


