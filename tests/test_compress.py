from __future__ import unicode_literals

import contextlib
import errno
import gzip
import os
import shutil
import tempfile
from unittest import TestCase

from whitenoise.compress import main as compress_main


COMPRESSABLE_FILE = 'application.css'
TOO_SMALL_FILE = 'too-small.css'
WRONG_EXTENSION = 'image.jpg'
TEST_FILES = {
    COMPRESSABLE_FILE: b'a' * 1000,
    TOO_SMALL_FILE: b'hi',
}


class CompressTestBase(TestCase):

    @classmethod
    def setUpClass(cls):
        # Make a temporary directory and copy in test files
        cls.tmp = tempfile.mkdtemp()
        for path, contents in TEST_FILES.items():
            path = os.path.join(cls.tmp, path.lstrip('/'))
            try:
                os.makedirs(os.path.dirname(path))
            except OSError as e:
                if e.errno != errno.EEXIST:
                    raise
            with open(path, 'wb') as f:
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
                gzip.open(
                    os.path.join(self.tmp, COMPRESSABLE_FILE + '.gz'), 'rb')) as f:
            contents = f.read()
        self.assertEqual(TEST_FILES[COMPRESSABLE_FILE], contents)

    def test_doesnt_compress_if_no_saving(self):
        self.assertFalse(os.path.exists(os.path.join(self.tmp, TOO_SMALL_FILE + 'gz')))

    def test_ignores_other_extensions(self):
        self.assertFalse(os.path.exists(os.path.join(self.tmp, WRONG_EXTENSION + '.gz')))

    def test_mtime_is_preserved(self):
        path = os.path.join(self.tmp, COMPRESSABLE_FILE)
        gzip_path = path + '.gz'
        self.assertEqual(os.path.getmtime(path), os.path.getmtime(gzip_path))
