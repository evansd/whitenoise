import os
from posixpath import basename
import re
import shutil
import sys
import tempfile

import django
from django.conf import settings
from django.contrib.staticfiles.storage import HashedFilesMixin, staticfiles_storage
from django.core.management import call_command
from django.test.utils import override_settings
from django.utils.functional import empty
import pytest

from whitenoise.storage import HelpfulExceptionMixin, MissingFileError

from .utils import Files


TEXT_TYPE = str if sys.version_info[0] >= 3 else unicode  # noqa: F821


@pytest.fixture()
def setup():
    django.setup()
    staticfiles_storage._wrapped = empty
    files = Files("static")
    tmp = TEXT_TYPE(tempfile.mkdtemp())
    settings.STATICFILES_DIRS = [files.directory]
    settings.STATIC_ROOT = tmp
    yield settings
    staticfiles_storage._wrapped = empty
    shutil.rmtree(tmp)


@pytest.fixture()
def _compressed_storage(setup):
    with override_settings(
        **{"STATICFILES_STORAGE": "whitenoise.storage.CompressedStaticFilesStorage"}
    ):
        call_command("collectstatic", verbosity=0, interactive=False)


@pytest.fixture()
def _compressed_manifest_storage(setup):
    with override_settings(
        **{
            "STATICFILES_STORAGE": "whitenoise.storage.CompressedManifestStaticFilesStorage",
            "WHITENOISE_KEEP_ONLY_HASHED_FILES": True,
        }
    ):
        call_command("collectstatic", verbosity=0, interactive=False)


def test_compressed_files_are_created(_compressed_storage):
    for name in ["styles.css.gz", "styles.css.br"]:
        path = os.path.join(settings.STATIC_ROOT, name)
        assert os.path.exists(path)


def test_make_helpful_exception(_compressed_manifest_storage):
    class TriggerException(HashedFilesMixin):
        def exists(self, path):
            return False

    exception = None
    try:
        TriggerException().hashed_name("/missing/file.png")
    except ValueError as e:
        exception = e
    helpful_exception = HelpfulExceptionMixin().make_helpful_exception(
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
