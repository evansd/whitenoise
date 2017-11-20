import os
from posixpath import basename
import re
import shutil
import sys
import tempfile

import django
from django.conf import settings
from django.contrib.staticfiles.storage import (
        HashedFilesMixin, staticfiles_storage)
from django.core.management import call_command
from django.test import SimpleTestCase
from django.test.utils import override_settings
from django.utils.functional import empty

from whitenoise.storage import HelpfulExceptionMixin, MissingFileError

from .utils import Files

django.setup()


TEXT_TYPE = str if sys.version_info[0] >= 3 else unicode


def reset_lazy_object(obj):
    obj._wrapped = empty


@override_settings()
class DjangoWhiteNoiseStorageTest(SimpleTestCase):

    @classmethod
    def setUpClass(cls):
        reset_lazy_object(staticfiles_storage)
        cls.files = Files('static')
        cls.tmp = TEXT_TYPE(tempfile.mkdtemp())
        settings.STATICFILES_DIRS = [cls.files.directory]
        settings.STATIC_ROOT = cls.tmp
        with override_settings(WHITENOISE_KEEP_ONLY_HASHED_FILES=True):
            call_command('collectstatic', verbosity=0, interactive=False)
        super(DjangoWhiteNoiseStorageTest, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        super(DjangoWhiteNoiseStorageTest, cls).tearDownClass()
        reset_lazy_object(staticfiles_storage)
        shutil.rmtree(cls.tmp)

    def test_make_helpful_exception(self):
        class TriggerException(HashedFilesMixin):
            def exists(self, path):
                return False
        exception = None
        try:
            TriggerException().hashed_name('/missing/file.png')
        except ValueError as e:
            exception = e
        helpful_exception = HelpfulExceptionMixin().make_helpful_exception(
                                exception,
                                'styles/app.css'
                            )
        self.assertIsInstance(helpful_exception, MissingFileError)

    def test_unversioned_files_are_deleted(self):
        name = 'styles.css'
        versioned_url = staticfiles_storage.url(name)
        versioned_name = basename(versioned_url)
        name_pattern = re.compile('^' + name.replace('.', r'\.([0-9a-f]+\.)?') + '$')
        remaining_files = [
                f for f in os.listdir(settings.STATIC_ROOT)
                if name_pattern.match(f)]
        self.assertEqual([versioned_name], remaining_files)
