from __future__ import unicode_literals

import contextlib
import errno
import gzip
import os
import re
import shutil
import tempfile
from unittest import TestCase

from whitenoise.compress import main as compress_main
from whitenoise.compress import Compressor


COMPRESSABLE_FILE = "application.css"
TOO_SMALL_FILE = "too-small.css"
WRONG_EXTENSION = "image.jpg"
TEST_FILES = {COMPRESSABLE_FILE: b"a" * 1000, TOO_SMALL_FILE: b"hi"}


class CompressTestBase(TestCase):
    @classmethod
    def setUpClass(cls):
        # Make a temporary directory and copy in test files
        cls.tmp = tempfile.mkdtemp()
        for path, contents in TEST_FILES.items():
            path = os.path.join(cls.tmp, path.lstrip("/"))
            try:
                os.makedirs(os.path.dirname(path))
            except OSError as e:
                if e.errno != errno.EEXIST:
                    raise
            with open(path, "wb") as f:
                f.write(contents)
            timestamp = 1498579535
            os.utime(path, (timestamp, timestamp))
        cls.run_compress()
        super(CompressTestBase, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        super(CompressTestBase, cls).tearDownClass()
        # Remove temporary directory
        shutil.rmtree(cls.tmp)


class CompressTest(CompressTestBase):
    @classmethod
    def run_compress(cls):
        compress_main(cls.tmp, quiet=True)

    def test_compresses_file(self):
        with contextlib.closing(
            gzip.open(os.path.join(self.tmp, COMPRESSABLE_FILE + ".gz"), "rb")
        ) as f:
            contents = f.read()
        self.assertEqual(TEST_FILES[COMPRESSABLE_FILE], contents)

    def test_doesnt_compress_if_no_saving(self):
        self.assertFalse(os.path.exists(os.path.join(self.tmp, TOO_SMALL_FILE + "gz")))

    def test_ignores_other_extensions(self):
        self.assertFalse(
            os.path.exists(os.path.join(self.tmp, WRONG_EXTENSION + ".gz"))
        )

    def test_mtime_is_preserved(self):
        path = os.path.join(self.tmp, COMPRESSABLE_FILE)
        gzip_path = path + ".gz"
        self.assertEqual(os.path.getmtime(path), os.path.getmtime(gzip_path))

    def test_with_custom_extensions(self):
        compressor = Compressor(extensions=["jpg"], quiet=True)
        self.assertEqual(
            compressor.extension_re, re.compile(r"\.(jpg)$", re.IGNORECASE)
        )

    def test_with_falsey_extensions(self):
        compressor = Compressor(quiet=True)
        self.assertEqual(compressor.get_extension_re(""), re.compile("^$"))

    def test_custom_log(self):
        compressor = Compressor(log="test")
        self.assertEqual(compressor.log, "test")

    def test_compress(self):
        compressor = Compressor(use_brotli=False, use_gzip=False)
        self.assertEqual(
            [], list(compressor.compress("tests/test_files/static/styles.css"))
        )

    def test_compressed_effectively_no_orig_size(self):
        compressor = Compressor(quiet=True)
        self.assertFalse(
            compressor.is_compressed_effectively(
                "test_encoding", "test_path", 0, "test_data"
            )
        )
