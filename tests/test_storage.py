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
from django.test import SimpleTestCase
from django.test.utils import override_settings
from django.utils.functional import empty

from whitenoise.storage import HelpfulExceptionMixin, MissingFileError

from .utils import Files

django.setup()


TEXT_TYPE = str if sys.version_info[0] >= 3 else unicode  # noqa: F821


def reset_lazy_object(obj):
    obj._wrapped = empty


@override_settings()
class StorageTestBase(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        reset_lazy_object(staticfiles_storage)
        cls.files = Files("static")
        cls.tmp = TEXT_TYPE(tempfile.mkdtemp())
        settings.STATICFILES_DIRS = [cls.files.directory]
        settings.STATIC_ROOT = cls.tmp
        with override_settings(**cls.get_settings()):
            call_command("collectstatic", verbosity=0, interactive=False)
        super(StorageTestBase, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        super(StorageTestBase, cls).tearDownClass()
        reset_lazy_object(staticfiles_storage)
        shutil.rmtree(cls.tmp)


class CompressedStaticFilesStorageTest(StorageTestBase):
    @classmethod
    def get_settings(self):
        return {
            "STATICFILES_STORAGE": "whitenoise.storage.CompressedStaticFilesStorage"
        }

    def test_compressed_files_are_created(self):
        for name in ["styles.css.gz", "styles.css.br"]:
            path = os.path.join(settings.STATIC_ROOT, name)
            self.assertTrue(os.path.exists(path))


class CompressedManifestStaticFilesStorageTest(StorageTestBase):
    @classmethod
    def get_settings(self):
        return {
            "STATICFILES_STORAGE": "whitenoise.storage.CompressedManifestStaticFilesStorage",
            "WHITENOISE_KEEP_ONLY_HASHED_FILES": True,
        }

    def test_make_helpful_exception(self):
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
        self.assertIsInstance(helpful_exception, MissingFileError)

    def test_unversioned_files_are_deleted(self):
        name = "styles.css"
        versioned_url = staticfiles_storage.url(name)
        versioned_name = basename(versioned_url)
        name_pattern = re.compile("^" + name.replace(".", r"\.([0-9a-f]+\.)?") + "$")
        remaining_files = [
            f for f in os.listdir(settings.STATIC_ROOT) if name_pattern.match(f)
        ]
        self.assertEqual([versioned_name], remaining_files)

    def test_manifest_file_is_left_in_place(self):
        manifest_file = os.path.join(settings.STATIC_ROOT, "staticfiles.json")
        self.assertTrue(os.path.exists(manifest_file))
