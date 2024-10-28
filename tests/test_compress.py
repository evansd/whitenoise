from __future__ import annotations

import contextlib
import gzip
import os
import re
import shutil
import tempfile
from unittest import mock

import pytest

from whitenoise.compress import Compressor
from whitenoise.compress import main as compress_main

COMPRESSABLE_FILE = "application.css"
TOO_SMALL_FILE = "too-small.css"
WRONG_EXTENSION = "image.jpg"
TEST_FILES = {COMPRESSABLE_FILE: b"a" * 1000, TOO_SMALL_FILE: b"hi"}


@pytest.fixture(scope="module", autouse=True)
def files_dir():
    # Make a temporary directory and copy in test files
    tmp = tempfile.mkdtemp()
    for path, contents in TEST_FILES.items():
        path = os.path.join(tmp, path.lstrip("/"))
        try:
            os.makedirs(os.path.dirname(path))
        except FileExistsError:
            pass
        with open(path, "wb") as f:
            f.write(contents)
        timestamp = 1498579535
        os.utime(path, (timestamp, timestamp))
    compress_main([tmp, "--quiet"])
    yield tmp
    shutil.rmtree(tmp)


def test_compresses_file(files_dir):
    with contextlib.closing(
        gzip.open(os.path.join(files_dir, COMPRESSABLE_FILE + ".gz"), "rb")
    ) as f:
        contents = f.read()
    assert TEST_FILES[COMPRESSABLE_FILE] == contents


def test_doesnt_compress_if_no_saving(files_dir):
    assert not os.path.exists(os.path.join(files_dir, TOO_SMALL_FILE + "gz"))


def test_ignores_other_extensions(files_dir):
    assert not os.path.exists(os.path.join(files_dir, WRONG_EXTENSION + ".gz"))


def test_mtime_is_preserved(files_dir):
    path = os.path.join(files_dir, COMPRESSABLE_FILE)
    gzip_path = path + ".gz"
    assert os.path.getmtime(path) == os.path.getmtime(gzip_path)


def test_with_custom_extensions():
    compressor = Compressor(extensions=["jpg"], quiet=True)
    assert compressor.extension_re == re.compile(r"\.(jpg)$", re.IGNORECASE)


def test_with_falsey_extensions():
    compressor = Compressor(quiet=True)
    assert compressor.get_extension_re("") == re.compile("^$")


def test_custom_log():
    compressor = Compressor(log="test")
    assert compressor.log == "test"


def test_compress():
    compressor = Compressor(use_brotli=False, use_gzip=False)
    assert [] == list(compressor.compress("tests/test_files/static/styles.css"))


def test_compressed_effectively_no_orig_size():
    compressor = Compressor(quiet=True)
    assert not compressor.is_compressed_effectively(
        "test_encoding", "test_path", 0, "test_data"
    )


def test_main_error(files_dir):
    with (
        pytest.raises(ValueError) as excinfo,
        mock.patch.object(Compressor, "compress", side_effect=ValueError("woops")),
    ):
        compress_main([files_dir, "--quiet"])

    assert excinfo.value.args == ("woops",)
