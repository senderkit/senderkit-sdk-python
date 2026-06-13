import pytest
import respx

from senderkit import SenderKit
from tests.helpers import BASE_URL, json_response, request_body

QUEUED = {"id": "msg_1", "status": "queued", "livemode": False}


@respx.mock
def test_send_basic(client):
    route = respx.post(f"{BASE_URL}/v1/send").mock(
        return_value=json_response(202, QUEUED)
    )
    result = client.send("welcome", "user@example.com", vars={"name": "Ada"})

    assert (result.id, result.status, result.livemode) == ("msg_1", "queued", False)
    request = route.calls.last.request
    assert request.headers["authorization"] == "Bearer sk_test_123"
    assert request.headers["user-agent"].startswith("senderkit-python/")
    assert request.headers["idempotency-key"]  # auto-generated
    assert request_body(request) == {
        "template": "welcome",
        "to": "user@example.com",
        "vars": {"name": "Ada"},
    }


@respx.mock
def test_send_custom_idempotency_key(client):
    route = respx.post(f"{BASE_URL}/v1/send").mock(
        return_value=json_response(202, QUEUED)
    )
    client.send("welcome", "user@example.com", idempotency_key="my-key")
    assert route.calls.last.request.headers["idempotency-key"] == "my-key"


@respx.mock
def test_send_serializes_envelope_and_datetime(client):
    from datetime import datetime

    route = respx.post(f"{BASE_URL}/v1/send").mock(
        return_value=json_response(202, QUEUED)
    )
    client.send(
        "welcome",
        "user@example.com",
        cc=["cc@example.com"],
        reply_to="reply@example.com",
        scheduled_at=datetime(2026, 1, 1, 9, 0, 0),
    )
    body = request_body(route.calls.last.request)
    assert body["cc"] == ["cc@example.com"]
    assert body["replyTo"] == "reply@example.com"
    assert body["scheduledAt"].startswith("2026-01-01T09:00:00")


def test_api_key_required():
    with pytest.raises(ValueError):
        SenderKit(api_key="")


def test_mode_detection():
    assert SenderKit(api_key="sk_test_x").mode == "test"
    assert SenderKit(api_key="sk_live_x").mode == "live"


@respx.mock
async def test_send_async(aclient):
    route = respx.post(f"{BASE_URL}/v1/send").mock(
        return_value=json_response(202, QUEUED)
    )
    result = await aclient.send("welcome", "user@example.com")
    assert result.id == "msg_1"
    assert route.calls.last.request.headers["idempotency-key"]
