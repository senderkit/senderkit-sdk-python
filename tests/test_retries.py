import httpx
import pytest
import respx

from senderkit.errors import ValidationError
from tests.helpers import BASE_URL

QUEUED = {"id": "msg_1", "status": "queued", "livemode": False}


@respx.mock
def test_retries_on_500_then_succeeds(client, no_backoff):
    route = respx.post(f"{BASE_URL}/v1/send").mock(
        side_effect=[
            httpx.Response(500),
            httpx.Response(503),
            httpx.Response(202, json=QUEUED),
        ]
    )
    result = client.send("welcome", "user@example.com")
    assert result.id == "msg_1"
    assert route.call_count == 3  # 1 + 2 retries


@respx.mock
def test_retries_on_429(client, no_backoff):
    route = respx.post(f"{BASE_URL}/v1/send").mock(
        side_effect=[
            httpx.Response(429, headers={"retry-after": "1"}),
            httpx.Response(202, json=QUEUED),
        ]
    )
    client.send("welcome", "user@example.com")
    assert route.call_count == 2


@respx.mock
def test_does_not_retry_400(client, no_backoff):
    route = respx.post(f"{BASE_URL}/v1/send").mock(
        return_value=httpx.Response(
            400, json={"error": {"code": "invalid_request", "message": "x"}}
        )
    )
    with pytest.raises(ValidationError):
        client.send("welcome", "user@example.com")
    assert route.call_count == 1


@respx.mock
def test_retries_network_error_then_succeeds(client, no_backoff):
    route = respx.post(f"{BASE_URL}/v1/send").mock(
        side_effect=[httpx.ConnectError("boom"), httpx.Response(202, json=QUEUED)]
    )
    result = client.send("welcome", "user@example.com")
    assert result.id == "msg_1"
    assert route.call_count == 2


@respx.mock
def test_exhausts_retries_and_raises(client, no_backoff):
    from senderkit.errors import APIError

    respx.post(f"{BASE_URL}/v1/send").mock(return_value=httpx.Response(500))
    with pytest.raises(APIError) as info:
        client.send("welcome", "user@example.com")
    assert info.value.status == 500
