from __future__ import annotations

import errno
import filecmp
import os
import re
import shutil
import textwrap
from collections.abc import Generator, Iterator
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any
from urllib.parse import urlsplit

from django.conf import settings
from django.contrib.staticfiles.storage import (
    ManifestStaticFilesStorage,
    StaticFilesStorage,
)

from whitenoise.compress import Compressor

_PostProcessT = Iterator[tuple[str, str, bool] | tuple[str, None, RuntimeError]]


class CompressedStaticFilesStorage(StaticFilesStorage):
    """
    StaticFilesStorage subclass that compresses output files.
    """

    def post_process(
        self, paths: dict[str, Any], dry_run: bool = False, **options: Any
    ) -> _PostProcessT:
        if dry_run:
            return

        extensions = getattr(settings, "WHITENOISE_SKIP_COMPRESS_EXTENSIONS", None)
        self.compressor = self.create_compressor(extensions=extensions, quiet=True)

        def _compress_path(path: str) -> Generator[tuple[str, str, bool]]:
            compressed: list[tuple[str, str, bool]] = []
            full_path = self.path(path)
            prefix_len = len(full_path) - len(path)
            for compressed_path in self.compressor.compress(full_path):
                compressed_name = compressed_path[prefix_len:]
                compressed.append((path, compressed_name, True))
            return compressed

        with ThreadPoolExecutor() as executor:
            futures = (
                executor.submit(_compress_path, path)
                for path in paths
                if self.compressor.should_compress(path)
            )
            for future in as_completed(futures):
                yield from future.result()

    def create_compressor(self, **kwargs: Any) -> Compressor:
        return Compressor(**kwargs)


class MissingFileError(ValueError):
    pass


class CompressedManifestStaticFilesStorage(ManifestStaticFilesStorage):
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

        # Make exception messages helpful
        for name, hashed_name, processed in files:
            if isinstance(processed, Exception):
                processed = self.make_helpful_exception(processed, name)
            yield name, hashed_name, processed

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
            self.delete_files((original_files | new_files) - hashed_files)
        compressed_names = {}
        for name, compressed_name in self.compress_files(hashed_files):
            compressed_names.setdefault(name, []).append(compressed_name)
            yield name, compressed_name, True
        if self.keep_only_hashed_files:
            return
        # Most unhashed files have the same content as their hashed copy, so
        # copy its compressed files rather than compressing it again.
        files_to_compress = []
        for name in original_files - hashed_files:
            hashed_name = hashed_names[name]
            if hashed_name in compressed_names and filecmp.cmp(
                self.path(name), self.path(hashed_name), shallow=False
            ):
                stat_result = os.stat(self.path(name))
                for compressed_name in compressed_names[hashed_name]:
                    copy_name = name + compressed_name[len(hashed_name) :]
                    shutil.copyfile(self.path(compressed_name), self.path(copy_name))
                    os.utime(
                        self.path(copy_name),
                        (stat_result.st_atime, stat_result.st_mtime),
                    )
                    yield name, copy_name, True
            else:
                files_to_compress.append(name)
        for name, compressed_name in self.compress_files(files_to_compress):
            yield name, compressed_name, True

    def hashed_name(self, *args, **kwargs):
        name = super().hashed_name(*args, **kwargs)
        if self._new_files is not None:
            self._new_files.add(urlsplit(self.clean_name(name)).path)
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

    def compress_files(self, paths):
        extensions = getattr(settings, "WHITENOISE_SKIP_COMPRESS_EXTENSIONS", None)
        self.compressor = self.create_compressor(extensions=extensions, quiet=True)

        def _compress_path(path: str) -> list[tuple[str, str]]:
            compressed: list[tuple[str, str]] = []
            full_path = self.path(path)
            prefix_len = len(full_path) - len(path)
            for compressed_path in self.compressor.compress(full_path):
                compressed_name = compressed_path[prefix_len:]
                compressed.append((path, compressed_name))
            return compressed

        with ThreadPoolExecutor() as executor:
            futures = (
                executor.submit(_compress_path, path)
                for path in paths
                if self.compressor.should_compress(path)
            )
            for future in as_completed(futures):
                yield from future.result()

    def make_helpful_exception(self, exception, name):
        """
        If a CSS file contains references to images, fonts etc that can't be found
        then Django's `post_process` blows up with a not particularly helpful
        ValueError that leads people to think WhiteNoise is broken.

        Here we attempt to intercept such errors and reformat them to be more
        helpful in revealing the source of the problem.
        """
        if isinstance(exception, ValueError):
            message = exception.args[0] if len(exception.args) else ""
            # Stringly typed exceptions. Yay!
            match = self._error_msg_re.search(message)
            if match:
                extension = os.path.splitext(name)[1].lstrip(".").upper()
                message = self._error_msg.format(
                    orig_message=message,
                    filename=name,
                    missing=match.group(1),
                    ext=extension,
                )
                exception = MissingFileError(message)
        return exception

    _error_msg_re = re.compile(r"^The file '(.+)' could not be found")

    _error_msg = textwrap.dedent(
        """\
        {orig_message}

        The {ext} file '{filename}' references a file which could not be found:
          {missing}

        Please check the URL references in this {ext} file, particularly any
        relative paths which might be pointing to the wrong location.
        """
    )
