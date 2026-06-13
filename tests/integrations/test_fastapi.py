import hashlib
import hmac

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from senderkit import WebhookEvent
from senderkit.integrations.fastapi import webhook_verifier


def _make_app(secret: str) -> FastAPI:
    app = FastAPI()
    verify = webhook_verifier(secret=secret, tolerance=10**12)

    @app.post("/webhooks")
    async def hook(event: WebhookEvent = Depends(verify)):  # noqa: B008
        return {"type": event.type, "payload": event.payload}

    return app


def _sign(body: bytes, ts: int, secret: str) -> str:
    digest = hmac.new(secret.encode(), f"{ts}.".encode() + body, hashlib.sha256).hexdigest()
    return f"t={ts},v1={digest}"


def test_webhook_dependency_accepts_valid_signature():
    client = TestClient(_make_app("whsec_test"))
    body = b'{"ok": true}'
    headers = {
        "X-SenderKit-Signature": _sign(body, 1000, "whsec_test"),
        "X-SenderKit-Event": "message.sent",
        "Content-Type": "application/json",
    }
    response = client.post("/webhooks", content=body, headers=headers)
    assert response.status_code == 200
    assert response.json() == {"type": "message.sent", "payload": {"ok": True}}


def test_webhook_dependency_rejects_bad_signature():
    client = TestClient(_make_app("whsec_test"))
    response = client.post(
        "/webhooks",
        content=b"{}",
        headers={"X-SenderKit-Signature": "t=1,v1=bad", "Content-Type": "application/json"},
    )
    assert response.status_code == 400


def test_get_senderkit_requires_api_key(monkeypatch):
    from senderkit.integrations import fastapi as integration

    integration.get_senderkit.cache_clear()
    monkeypatch.delenv("SENDERKIT_API_KEY", raising=False)
    with pytest.raises(RuntimeError):
        integration.get_senderkit()


def test_get_senderkit_builds_from_env(monkeypatch):
    from senderkit import AsyncSenderKit
    from senderkit.integrations import fastapi as integration

    integration.get_senderkit.cache_clear()
    monkeypatch.setenv("SENDERKIT_API_KEY", "sk_test_env")
    sk = integration.get_senderkit()
    assert isinstance(sk, AsyncSenderKit)
    assert sk.mode == "test"
    integration.get_senderkit.cache_clear()
