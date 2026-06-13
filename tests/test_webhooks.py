import hashlib
import hmac
import json

import pytest

from senderkit import WebhookVerifier
from senderkit.errors import SignatureVerificationError

SECRET = "whsec_test"


def _sign(body: str, timestamp: int, secret: str = SECRET) -> str:
    digest = hmac.new(secret.encode(), f"{timestamp}.{body}".encode(), hashlib.sha256).hexdigest()
    return f"t={timestamp},v1={digest}"


def test_verify_valid():
    body = json.dumps({"type": "message.delivered", "id": "msg_1"})
    header = _sign(body, 1000)
    event = WebhookVerifier(SECRET).verify(
        body, header, now=1000, event_type="message.delivered", delivery_id="dl_1"
    )
    assert event.type == "message.delivered"
    assert event.delivery_id == "dl_1"
    assert event.payload["id"] == "msg_1"
    assert event.timestamp == 1000


def test_verify_accepts_bytes():
    body = b'{"ok": true}'
    header = _sign(body.decode(), 1000)
    event = WebhookVerifier(SECRET).verify(body, header, now=1000)
    assert event.payload == {"ok": True}


def test_bad_signature():
    body = "{}"
    header = _sign(body, 1000, secret="wrong")
    with pytest.raises(SignatureVerificationError, match="mismatch"):
        WebhookVerifier(SECRET).verify(body, header, now=1000)


def test_stale_timestamp():
    body = "{}"
    header = _sign(body, 1000)
    with pytest.raises(SignatureVerificationError, match="tolerance"):
        WebhookVerifier(SECRET).verify(body, header, now=2000, tolerance=300)


def test_malformed_header():
    with pytest.raises(SignatureVerificationError, match="Malformed"):
        WebhookVerifier(SECRET).verify("{}", "garbage", now=1000)


def test_empty_secret():
    with pytest.raises(SignatureVerificationError, match="secret"):
        WebhookVerifier("").verify("{}", "t=1,v1=abc", now=1)


def test_secret_override_per_call():
    body = "{}"
    header = _sign(body, 1000, secret="other")
    event = WebhookVerifier(SECRET).verify(body, header, secret="other", now=1000)
    assert event.timestamp == 1000


def test_non_json_body_yields_empty_payload():
    body = "not json"
    header = _sign(body, 1000)
    event = WebhookVerifier(SECRET).verify(body, header, now=1000)
    assert event.payload == {}
