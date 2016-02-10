from django.contrib.staticfiles.storage import HashedFilesMixin
from django.test import SimpleTestCase
from django.test.utils import override_settings

from whitenoise.storage import HelpfulExceptionMixin, MissingFileError


@override_settings()
class DjangoWhiteNoiseStorageTest(SimpleTestCase):

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
