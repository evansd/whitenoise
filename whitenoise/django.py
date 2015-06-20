from __future__ import absolute_import

import os.path
import re
import textwrap

try:
    import urlparse
except ImportError:
    import urllib.parse as urlparse

from django.conf import settings as settings
from django.core.exceptions import ImproperlyConfigured
from django.contrib.staticfiles.storage import staticfiles_storage
from django.contrib.staticfiles import finders
try:
    from django.contrib.staticfiles.storage import ManifestStaticFilesStorage
except ImportError:
    # For Django versions < 1.7
    from .storage_backport import ManifestStaticFilesStorage

from .base import WhiteNoise, format_prefix
from .gzip import compress, extension_regex, GZIP_EXCLUDE_EXTENSIONS


def get_prefix_from_url(url):
    return format_prefix(urlparse.urlparse(url).path)


class DjangoWhiteNoise(WhiteNoise):

    config_attrs = WhiteNoise.config_attrs + ('root', 'use_finders')
    root = None
    use_finders = False

    def __init__(self, application, settings=settings):
        self.configure_from_settings(settings)
        super(DjangoWhiteNoise, self).__init__(application)
        self.add_files(self.static_root, prefix=self.static_prefix)
        if self.root:
            self.add_files(self.root)

    def configure_from_settings(self, settings):
        # Default configuration
        self.charset = settings.FILE_CHARSET
        self.autorefresh = settings.DEBUG
        self.use_finders = settings.DEBUG
        if settings.DEBUG:
            self.max_age = 0
        # Allow settings to override default attributes
        for attr in self.config_attrs:
            settings_key = 'WHITENOISE_{}'.format(attr.upper())
            try:
                setattr(self, attr, getattr(settings, settings_key))
            except AttributeError:
                pass
        self.static_prefix = get_prefix_from_url(
                getattr(settings, 'STATIC_URL', ''))
        self.static_root = getattr(settings, 'STATIC_ROOT', None)
        if not self.static_root or self.static_prefix == '/':
            raise ImproperlyConfigured('Both STATIC_URL and STATIC_ROOT '
                    'settings must be configured to use DjangoWhiteNoise')
        if self.use_finders and not self.autorefresh:
            raise ImproperlyConfigured('WHITENOISE_USE_FINDERS can only be '
                    'enabled in development when WHITENOISE_AUTOREFRESH is '
                    'also enabled.')

    def find_file(self, url):
        if self.use_finders and url.startswith(self.static_prefix):
            path = finders.find(url[len(self.static_prefix):])
            if path:
                return self.get_static_file(path, url)
        return super(DjangoWhiteNoise, self).find_file(url)

    def is_immutable_file(self, path, url):
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


class MissingFileError(ValueError):
    pass


class GzipStaticFilesMixin(object):
    """
    Wraps a StaticFilesStorage instance to create gzipped versions of its
    output files
    """

    def post_process(self, *args, **kwargs):
        files = super(GzipStaticFilesMixin, self).post_process(*args, **kwargs)
        dry_run = kwargs.get('dry_run', False)
        extensions = getattr(settings, 'WHITENOISE_GZIP_EXCLUDE_EXTENSIONS',
                GZIP_EXCLUDE_EXTENSIONS)
        excluded_re = extension_regex(extensions)
        for name, hashed_name, processed in files:
            if (not dry_run and not excluded_re.search(name) and not
                    isinstance(processed, Exception)):
                compress(self.path(name))
                if hashed_name is not None:
                    compress(self.path(hashed_name))
            yield name, hashed_name, processed


class HelpfulExceptionMixin(object):
    """
    If a CSS file contains references to images, fonts etc that can't be found
    then Django's `post_process` blows up with a not particularly helpful
    ValueError that leads people to think WhiteNoise is broken.

    Here we attempt to intercept such errors and reformat them to be more
    helpful in revealing the source of the problem.
    """

    ERROR_MSG_RE = re.compile("^The file '(.+)' could not be found")

    ERROR_MSG = textwrap.dedent(u"""\
        {orig_message}

        The {ext} file '{filename}' references a file which could not be found:
          {missing}

        Please check the URL references in this {ext} file, particularly any
        relative paths which might be pointing to the wrong location.
        """)

    def post_process(self, *args, **kwargs):
        files = super(HelpfulExceptionMixin, self).post_process(*args, **kwargs)
        for name, hashed_name, processed in files:
            if isinstance(processed, Exception):
                processed = self.make_helpful_exception(processed, name)
            yield name, hashed_name, processed

    def make_helpful_exception(self, exception, name):
        if isinstance(exception, ValueError):
            message = exception.args[0] if len(exception.args) else ''
            # Stringly typed exceptions. Yay!
            match = self.ERROR_MSG_RE.search(message)
            if match:
                extension = os.path.splitext(name)[1].lstrip('.').upper()
                message = self.ERROR_MSG.format(
                        orig_message=message,
                        filename=name,
                        missing=match.group(1),
                        ext=extension)
                exception = MissingFileError(message)
        return exception


class GzipManifestStaticFilesStorage(
        HelpfulExceptionMixin, GzipStaticFilesMixin,
        ManifestStaticFilesStorage):
    pass
