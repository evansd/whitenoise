from __future__ import annotations

import errno
import os
import re
import textwrap

from django.conf import settings
from django.contrib.staticfiles.storage import (
    ManifestStaticFilesStorage,
    StaticFilesStorage,
)

from .compress import Compressor


class CompressedStaticFilesMixin:
    """
    Wraps a StaticFilesStorage instance to compress output files
    """

    def post_process(self, *args, **kwargs):
        super_post_process = getattr(
            super(),
            "post_process",
            self.fallback_post_process,
        )
        files = super_post_process(*args, **kwargs)
        if not kwargs.get("dry_run"):
            files = self.post_process_with_compression(files)
        return files

    # Only used if the class we're wrapping doesn't implement its own
    # `post_process` method
    def fallback_post_process(self, paths, dry_run=False, **options):
        if not dry_run:
            for path in paths:
                yield path, None, False

    def create_compressor(self, **kwargs):
        return Compressor(**kwargs)

    def post_process_with_compression(self, files):
        extensions = getattr(settings, "WHITENOISE_SKIP_COMPRESS_EXTENSIONS", None)
        compressor = self.create_compressor(extensions=extensions, quiet=True)
        for name, hashed_name, processed in files:
            yield name, hashed_name, processed
            if isinstance(processed, Exception):
                continue
            unique_names = set(filter(None, [name, hashed_name]))
            for name in unique_names:
                if compressor.should_compress(name):
                    path = self.path(name)
                    prefix_len = len(path) - len(name)
                    for compressed_path in compressor.compress(path):
                        compressed_name = compressed_path[prefix_len:]
                        yield name, compressed_name, True


class CompressedStaticFilesStorage(CompressedStaticFilesMixin, StaticFilesStorage):
    pass


class HelpfulExceptionMixin:
    """
    If a CSS file contains references to images, fonts etc that can't be found
    then Django's `post_process` blows up with a not particularly helpful
    ValueError that leads people to think WhiteNoise is broken.

    Here we attempt to intercept such errors and reformat them to be more
    helpful in revealing the source of the problem.
    """

    ERROR_MSG_RE = re.compile("^The file '(.+)' could not be found")

    ERROR_MSG = textwrap.dedent(
        """\
        {orig_message}

        The {ext} file '{filename}' references a file which could not be found:
          {missing}

        Please check the URL references in this {ext} file, particularly any
        relative paths which might be pointing to the wrong location.
        """
    )

    def post_process(self, *args, **kwargs):
        files = super().post_process(*args, **kwargs)
        for name, hashed_name, processed in files:
            if isinstance(processed, Exception):
                processed = self.make_helpful_exception(processed, name)
            yield name, hashed_name, processed

    def make_helpful_exception(self, exception, name):
        if isinstance(exception, ValueError):
            message = exception.args[0] if len(exception.args) else ""
            # Stringly typed exceptions. Yay!
            match = self.ERROR_MSG_RE.search(message)
            if match:
                extension = os.path.splitext(name)[1].lstrip(".").upper()
                message = self.ERROR_MSG.format(
                    orig_message=message,
                    filename=name,
                    missing=match.group(1),
                    ext=extension,
                )
                exception = MissingFileError(message)
        return exception


class MissingFileError(ValueError):
    pass


class CompressedManifestStaticFilesStorage(
    HelpfulExceptionMixin, ManifestStaticFilesStorage
):
    """
    Extends ManifestStaticFilesStorage instance to create compressed versions
    of its output files and, optionally, to delete the non-hashed files (i.e.
    those without the hash in their name)
    """

    _new_files = None

    def __init__(self, *args, **kwargs):
        manifest_strict = getattr(settings, "WHITENOISE_MANIFEST_STRICT", None)
        if manifest_strict is not None:
            self.manifest_strict = manifest_strict
        super().__init__(*args, **kwargs)

    def post_process(self, *args, **kwargs):
        files = super().post_process(*args, **kwargs)
        if not kwargs.get("dry_run"):
            files = self.post_process_with_compression(files)
        return files

    def post_process_with_compression(self, files):
        # Files may get hashed multiple times, we want to keep track of all the
        # intermediate files generated during the process and which of these
        # are the final names used for each file. As not every intermediate
        # file is yielded we have to hook in to the `hashed_name` method to
        # keep track of them all.
        hashed_names = {}
        new_files = set()
        self.start_tracking_new_files(new_files)
        for name, hashed_name, processed in files:
            if hashed_name and not isinstance(processed, Exception):
                hashed_names[self.clean_name(name)] = hashed_name
            yield name, hashed_name, processed
        self.stop_tracking_new_files()
        original_files = set(hashed_names.keys())
        hashed_files = set(hashed_names.values())
        if self.keep_only_hashed_files:
            files_to_delete = (original_files | new_files) - hashed_files
            files_to_compress = hashed_files
        else:
            files_to_delete = set()
            files_to_compress = original_files | hashed_files
        self.delete_files(files_to_delete)
        for name, compressed_name in self.compress_files(files_to_compress):
            yield name, compressed_name, True

    def hashed_name(self, *args, **kwargs):
        name = super().hashed_name(*args, **kwargs)
        if self._new_files is not None:
            self._new_files.add(self.clean_name(name))
        return name

    def start_tracking_new_files(self, new_files):
        self._new_files = new_files

    def stop_tracking_new_files(self):
        self._new_files = None

    @property
    def keep_only_hashed_files(self):
        return getattr(settings, "WHITENOISE_KEEP_ONLY_HASHED_FILES", False)

    def delete_files(self, files_to_delete):
        for name in files_to_delete:
            try:
                os.unlink(self.path(name))
            except OSError as e:
                if e.errno != errno.ENOENT:
                    raise

    def create_compressor(self, **kwargs):
        return Compressor(**kwargs)

    def compress_files(self, names):
        extensions = getattr(settings, "WHITENOISE_SKIP_COMPRESS_EXTENSIONS", None)
        compressor = self.create_compressor(extensions=extensions, quiet=True)
        for name in names:
            if compressor.should_compress(name):
                path = self.path(name)
                prefix_len = len(path) - len(name)
                for compressed_path in compressor.compress(path):
                    compressed_name = compressed_path[prefix_len:]
                    yield name, compressed_name
