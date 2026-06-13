import httpx
import pytest
import respx

from senderkit import errors
from tests.helpers import BASE_URL


@respx.mock
def test_timeout_raises_and_is_not_retried(client):
    route = respx.post(f"{BASE_URL}/v1/send").mock(
        side_effect=httpx.ReadTimeout("slow")
    )
    with pytest.raises(errors.TimeoutError):
        client.send("welcome", "user@example.com")
    assert route.call_count == 1  # timeouts are terminal


@respx.mock
def test_network_error_raises_after_exhaustion(client, no_backoff):
    respx.get(f"{BASE_URL}/v1/context").mock(side_effect=httpx.ConnectError("down"))
    with pytest.raises(errors.NetworkError):
        client.context()
