from __future__ import annotations

import os

import django
import pytest


@pytest.fixture(autouse=True, scope="session")
def django_setup():
    os.environ["DJANGO_SETTINGS_MODULE"] = "tests.django_settings"
    django.setup()
    yield
