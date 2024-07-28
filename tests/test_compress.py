from __future__ import annotations

import contextlib
import gzip
import os
import re
import shutil
import tempfile

import pytest

from django.test import override_settings
from whitenoise.compress import Compressor
from whitenoise.compress import main as compress_main

from . import custom_compressor

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


def test_default_compressor(files_dir):
    # Run the compression command with default compressor
    custom_compressor.called = False

    compress_main([files_dir])

    for path in TEST_FILES.keys():
        full_path = os.path.join(files_dir, path)
        if path.endswith(".jpg"):
            assert not os.path.exists(full_path + ".gz")
        else:
            if TOO_SMALL_FILE not in full_path:
                assert os.path.exists(full_path + ".gz")

    assert custom_compressor.called is False


def test_custom_compressor(files_dir):
    custom_compressor.called = False

    # Run the compression command with the custom compressor
    compress_main([files_dir, "--compressor-class=tests.custom_compressor.CustomCompressor"])

    assert custom_compressor.called is True

    for path in TEST_FILES.keys():
        full_path = os.path.join(files_dir, path)
        if path.endswith(".jpg"):
            assert not os.path.exists(full_path + ".gz")
        else:
            if TOO_SMALL_FILE not in full_path:
                assert os.path.exists(full_path + ".gz")


@override_settings(WHITENOISE_COMPRESSOR_CLASS='tests.custom_compressor.CustomCompressor')
def test_custom_compressor_settings(files_dir):
    """ Test if the custom compressor can be set via WHITENOISE_COMPRESSOR_CLASS settings """
    custom_compressor.called = False

    compress_main([files_dir])

    assert custom_compressor.called is True

    for path in TEST_FILES.keys():
        full_path = os.path.join(files_dir, path)
        if path.endswith(".jpg"):
            assert not os.path.exists(full_path + ".gz")
        else:
            if TOO_SMALL_FILE not in full_path:
                assert os.path.exists(full_path + ".gz")
