from __future__ import annotations

import asyncio

import pytest


@pytest.fixture()
def loop():
    return asyncio.get_event_loop()
