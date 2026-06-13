import httpx
import pytest
import respx

from senderkit import errors
from tests.helpers import BASE_URL


@pytest.mark.parametrize(
    "status,expected",
    [
        (400, errors.ValidationError),
        (401, errors.AuthenticationError),
        (403, errors.AuthenticationError),
        (402, errors.PaymentRequiredError),
        (422, errors.ValidationError),
        (429, errors.RateLimitError),
        (500, errors.APIError),
    ],
)
@respx.mock
def test_status_maps_to_error_class(status, expected, no_backoff):
    from senderkit import SenderKit
    from tests.helpers import API_KEY

    sk = SenderKit(api_key=API_KEY, base_url=BASE_URL, max_retries=0)
    respx.post(f"{BASE_URL}/v1/send").mock(
        return_value=httpx.Response(
            status,
            json={"error": {"code": "some_code", "message": "nope", "issues": [{"x": 1}]}},
            headers={"x-request-id": "req_123", "retry-after": "5"},
        )
    )
    with pytest.raises(expected) as info:
        sk.send("welcome", "user@example.com")

    exc = info.value
    assert isinstance(exc, errors.SenderKitError)
    assert exc.status == status
    assert exc.code == "some_code"
    assert exc.request_id == "req_123"
    assert exc.issues == [{"x": 1}]
    if isinstance(exc, errors.RateLimitError):
        assert exc.retry_after == 5.0
    sk.close()


@respx.mock
def test_error_without_body(client, no_backoff):
    respx.get(f"{BASE_URL}/v1/context").mock(return_value=httpx.Response(404))
    with pytest.raises(errors.APIError) as info:
        client.context()
    assert info.value.status == 404
    assert info.value.message if hasattr(info.value, "message") else str(info.value)
