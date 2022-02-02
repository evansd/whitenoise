from __future__ import annotations

import gzip
import os
import re
from io import BytesIO

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.module_loading import import_string

try:
    import brotli

    brotli_installed = True
except ImportError:
    brotli_installed = False


class Compressor:

    # Extensions that it's not worth trying to compress
    SKIP_COMPRESS_EXTENSIONS = (
        # Images
        "jpg",
        "jpeg",
        "png",
        "gif",
        "webp",
        # Compressed files
        "zip",
        "gz",
        "tgz",
        "bz2",
        "tbz",
        "xz",
        "br",
        # Flash
        "swf",
        "flv",
        # Fonts
        "woff",
        "woff2",
    )

    def __init__(
        self,
        extensions=None,
        use_gzip=True,
        use_brotli=True,
        skip_regexp=False,
        log=print,
        quiet=False,
    ):
        if extensions is None:
            extensions = self.SKIP_COMPRESS_EXTENSIONS
        self.extension_re = self.get_extension_re(extensions)
        self.use_gzip = use_gzip
        self.use_brotli = use_brotli and brotli_installed
        self.skip_regexp = skip_regexp
        if not quiet:
            self.log = log

    @staticmethod
    def get_extension_re(extensions):
        if not extensions:
            return re.compile("^$")
        else:
            return re.compile(
                r"\.({})$".format("|".join(map(re.escape, extensions))), re.IGNORECASE
            )

    def should_compress(self, filename):
        if self.skip_regexp is False:
            skip_regexp = getattr(settings, "WHITENOISE_SKIP_REGEXP", [])
        else:
            skip_regexp = self.skip_regexp
        skip = False
        for r in skip_regexp:
            if re.match(r, filename):
                skip = True
                break
        return not self.extension_re.search(filename) and not skip

    def log(self, message):
        pass

    def compress(self, path):
        with open(path, "rb") as f:
            stat_result = os.fstat(f.fileno())
            data = f.read()
        size = len(data)
        if self.use_brotli:
            compressed = self.compress_brotli(data)
            if self.is_compressed_effectively("Brotli", path, size, compressed):
                yield self.write_data(path, compressed, ".br", stat_result)
            else:
                # If Brotli compression wasn't effective gzip won't be either
                return
        if self.use_gzip:
            compressed = self.compress_gzip(data)
            if self.is_compressed_effectively("Gzip", path, size, compressed):
                yield self.write_data(path, compressed, ".gz", stat_result)

    @staticmethod
    def compress_gzip(data):
        output = BytesIO()
        # Explicitly set mtime to 0 so gzip content is fully determined
        # by file content (0 = "no timestamp" according to gzip spec)
        with gzip.GzipFile(
            filename="", mode="wb", fileobj=output, compresslevel=9, mtime=0
        ) as gz_file:
            gz_file.write(data)
        return output.getvalue()

    @staticmethod
    def compress_brotli(data):
        return brotli.compress(data)

    def is_compressed_effectively(self, encoding_name, path, orig_size, data):
        compressed_size = len(data)
        if orig_size == 0:
            is_effective = False
        else:
            ratio = compressed_size / orig_size
            is_effective = ratio <= 0.95
        if is_effective:
            self.log(
                "{} compressed {} ({}K -> {}K)".format(
                    encoding_name, path, orig_size // 1024, compressed_size // 1024
                )
            )
        else:
            self.log(f"Skipping {path} ({encoding_name} compression not effective)")
        return is_effective

    def write_data(self, path, data, suffix, stat_result):
        filename = path + suffix
        with open(filename, "wb") as f:
            f.write(data)
        os.utime(filename, (stat_result.st_atime, stat_result.st_mtime))
        return filename


try:
    compressor_class = import_string(
        getattr(
            settings, "WHITENOISE_COMPRESSOR_CLASS", "whitenoise.compress.Compressor"
        ),
    )
except ImproperlyConfigured:
    compressor_class = Compressor


def main(root, **kwargs):
    compressor_class_str = kwargs.pop(
        "compressor_class", "whitenoise.compress.Compressor"
    )
    compressor_class = import_string(compressor_class_str)
    compressor = compressor_class(**kwargs)
    for dirpath, _dirs, files in os.walk(root):
        for filename in files:
            if compressor.should_compress(filename):
                path = os.path.join(dirpath, filename)
                for _compressed in compressor.compress(path):
                    pass


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Search for all files inside <root> *not* matching "
        "<extensions> and produce compressed versions with "
        "'.gz' and '.br' suffixes (as long as this results in a "
        "smaller file)"
    )
    parser.add_argument(
        "-q", "--quiet", help="Don't produce log output", action="store_true"
    )
    parser.add_argument(
        "--no-gzip",
        help="Don't produce gzip '.gz' files",
        action="store_false",
        dest="use_gzip",
    )
    parser.add_argument(
        "--no-brotli",
        help="Don't produce brotli '.br' files",
        action="store_false",
        dest="use_brotli",
    )
    parser.add_argument("root", help="Path root from which to search for files")
    parser.add_argument(
        "extensions",
        nargs="*",
        help="File extensions to exclude from compression "
        "(default: {})".format(", ".join(compressor_class.SKIP_COMPRESS_EXTENSIONS)),
        default=compressor_class.SKIP_COMPRESS_EXTENSIONS,
    )
    parser.add_argument(
        "--compressor-class",
        nargs="*",
        help="Path to compressor class",
        dest="compressor_class",
        default="whitenoise.compress.Compressor",
    )
    parser.add_argument(
        "--skip-regexp",
        nargs="*",
        help="File regexp patterns to exclude from compression",
        dest="skip_regexp",
        default="",
    )
    args = parser.parse_args()
    main(**vars(args))
