from __future__ import absolute_import

import os
import re
import textwrap

from django.conf import settings
from django.contrib.staticfiles.storage import ManifestStaticFilesStorage
from django.utils.functional import cached_property

from .gzip import compress, extension_regex, GZIP_EXCLUDE_EXTENSIONS


class CompressedStaticFilesMixin(object):
    """
    Wraps a StaticFilesStorage instance to create gzipped versions of its
    output files
    """

    def post_process(self, *args, **kwargs):
        files = super(CompressedStaticFilesMixin, self).post_process(*args, **kwargs)
        for name, hashed_name, processed in files:
            if self.is_compressible(name, hashed_name, processed, **kwargs):
                self.compress(self.path(name))
                if hashed_name is not None:
                    compress(self.path(hashed_name))
            yield name, hashed_name, processed

    def is_compressible(self, name, hashed_name, processed, dry_run=False, **kwargs):
        if dry_run:
            return False
        if isinstance(processed, Exception):
            return False
        else:
            return not self.excluded_extension_regex.search(name)

    def compress(self, path):
        compress(path)

    @cached_property
    def excluded_extension_regex(self):
        extensions = getattr(settings, 'WHITENOISE_GZIP_EXCLUDE_EXTENSIONS',
                GZIP_EXCLUDE_EXTENSIONS)
        return extension_regex(extensions)



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


class MissingFileError(ValueError):
    pass


class CompressedManifestStaticFilesStorage(
        HelpfulExceptionMixin, CompressedStaticFilesMixin,
        ManifestStaticFilesStorage):
    pass
