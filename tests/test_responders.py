from __future__ import annotations

from io import BytesIO

from django.test import SimpleTestCase

from whitenoise.responders import SlicedFile


class SlicedFileTests(SimpleTestCase):
    def test_close_does_not_rerun_on_del(self):
        """
        Regression test for the subtle close() behaviour of SlicedFile that
        could lead to database connection errors.

        https://github.com/evansd/whitenoise/pull/612
        """
        file = BytesIO(b"1234567890")
        sliced_file = SlicedFile(file, 1, 2)

        # Emulate how Django patches the file object's close() method to be
        # response.close() and count the calls.
        # https://github.com/django/django/blob/345a6652e6a15febbf4f68351dcea5dd674ea324/django/core/handlers/wsgi.py#L137-L140
        calls = 0

        file_close = sliced_file.close

        def closer():
            nonlocal calls, file_close
            calls += 1
            if file_close is not None:
                file_close()
                file_close = None

        sliced_file.close = closer

        sliced_file.close()
        assert calls == 1

        # Deleting the sliced file should not call close again.
        del sliced_file
        assert calls == 1
