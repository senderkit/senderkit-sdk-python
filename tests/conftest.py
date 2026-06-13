"""Pytest fixtures: sync/async clients pointed at the mock base URL, plus a
fixture that disables retry backoff so retry tests run instantly."""

from __future__ import annotations

import pytest

from senderkit import AsyncSenderKit, SenderKit
from tests.helpers import API_KEY, BASE_URL


@pytest.fixture
def client():
    sk = SenderKit(api_key=API_KEY, base_url=BASE_URL, max_retries=2)
    yield sk
    sk.close()


@pytest.fixture
async def aclient():
    sk = AsyncSenderKit(api_key=API_KEY, base_url=BASE_URL, max_retries=2)
    yield sk
    await sk.aclose()


@pytest.fixture
def no_backoff(monkeypatch):
    monkeypatch.setattr("senderkit._http._backoff_seconds", lambda *a, **k: 0)
