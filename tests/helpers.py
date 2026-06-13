"""Shared constants and small helpers for the test suite."""

from __future__ import annotations

import json
from typing import Any

import httpx

BASE_URL = "https://api.test"
API_KEY = "sk_test_123"


def json_response(status: int, payload: Any) -> httpx.Response:
    return httpx.Response(status, json=payload)


def request_body(request: httpx.Request) -> dict:
    return json.loads(request.content)
