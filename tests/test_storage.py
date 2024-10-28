from __future__ import annotations

import os
import re
import shutil
import tempfile
from posixpath import basename

import pytest
from django.conf import settings
from django.contrib.staticfiles.storage import HashedFilesMixin
from django.contrib.staticfiles.storage import staticfiles_storage
from django.core.management import call_command
from django.test.utils import override_settings
from django.utils.functional import empty

from tests.utils import Files
from whitenoise.storage import CompressedManifestStaticFilesStorage
from whitenoise.storage import MissingFileError


@pytest.fixture()
def setup():
    staticfiles_storage._wrapped = empty
    files = Files("static")
    tmp = tempfile.mkdtemp()
    with override_settings(
        STATICFILES_DIRS=[files.directory],
        STATIC_ROOT=tmp,
    ):
        yield settings
    staticfiles_storage._wrapped = empty
    shutil.rmtree(tmp)


@pytest.fixture()
def _compressed_storage(setup):
    backend = "whitenoise.storage.CompressedStaticFilesStorage"
    storages = {
        "STORAGES": {
            **settings.STORAGES,
            "staticfiles": {"BACKEND": backend},
        }
    }

    with override_settings(**storages):
        yield


@pytest.fixture()
def _compressed_manifest_storage(setup):
    backend = "whitenoise.storage.CompressedManifestStaticFilesStorage"
    storages = {
        "STORAGES": {
            **settings.STORAGES,
            "staticfiles": {"BACKEND": backend},
        }
    }

    with override_settings(**storages, WHITENOISE_KEEP_ONLY_HASHED_FILES=True):
        call_command("collectstatic", verbosity=0, interactive=False)


def test_compressed_static_files_storage(_compressed_storage):
    call_command("collectstatic", verbosity=0, interactive=False)

    for name in ["styles.css.gz", "styles.css.br"]:
        path = os.path.join(settings.STATIC_ROOT, name)
        assert os.path.exists(path)


def test_compressed_static_files_storage_dry_run(_compressed_storage):
    call_command("collectstatic", "--dry-run", verbosity=0, interactive=False)

    for name in ["styles.css.gz", "styles.css.br"]:
        path = os.path.join(settings.STATIC_ROOT, name)
        assert not os.path.exists(path)


def test_make_helpful_exception(_compressed_manifest_storage):
    class TriggerException(HashedFilesMixin):
        def exists(self, path):
            return False

    exception = None
    try:
        TriggerException().hashed_name("/missing/file.png")
    except ValueError as e:
        exception = e
    helpful_exception = CompressedManifestStaticFilesStorage().make_helpful_exception(
        exception, "styles/app.css"
    )
    assert isinstance(helpful_exception, MissingFileError)


def test_unversioned_files_are_deleted(_compressed_manifest_storage):
    name = "styles.css"
    versioned_url = staticfiles_storage.url(name)
    versioned_name = basename(versioned_url)
    name_pattern = re.compile("^" + name.replace(".", r"\.([0-9a-f]+\.)?") + "$")
    remaining_files = [
        f for f in os.listdir(settings.STATIC_ROOT) if name_pattern.match(f)
    ]
    assert [versioned_name] == remaining_files


def test_manifest_file_is_left_in_place(_compressed_manifest_storage):
    manifest_file = os.path.join(settings.STATIC_ROOT, "staticfiles.json")
    assert os.path.exists(manifest_file)


def test_manifest_strict_attribute_is_set():
    with override_settings(WHITENOISE_MANIFEST_STRICT=True):
        storage = CompressedManifestStaticFilesStorage()
        assert storage.manifest_strict is True
    with override_settings(WHITENOISE_MANIFEST_STRICT=False):
        storage = CompressedManifestStaticFilesStorage()
        assert storage.manifest_strict is False
