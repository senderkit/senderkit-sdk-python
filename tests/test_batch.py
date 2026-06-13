import httpx
import respx

from senderkit import TemplateSend
from senderkit.errors import ValidationError
from tests.helpers import BASE_URL, request_body


def _handler(request: httpx.Request) -> httpx.Response:
    body = request_body(request)
    if body["to"] == "bad@example.com":
        return httpx.Response(422, json={"error": {"code": "invalid_request", "message": "bad"}})
    return httpx.Response(202, json={"id": "msg", "status": "queued", "livemode": False})


@respx.mock
def test_batch_mixed_success_and_failure(client):
    respx.post(f"{BASE_URL}/v1/send").mock(side_effect=_handler)
    requests = [
        TemplateSend(template="welcome", to="ok1@example.com"),
        TemplateSend(template="welcome", to="bad@example.com"),
        TemplateSend(template="welcome", to="ok2@example.com"),
    ]
    results = client.send_batch(requests, concurrency=3)

    assert [r.index for r in results] == [0, 1, 2]  # positionally aligned
    assert results[0].ok and results[0].result.status == "queued"
    assert results[2].ok
    assert results[1].ok is False
    assert isinstance(results[1].error, ValidationError)


@respx.mock
def test_batch_per_index_idempotency_keys(client):
    route = respx.post(f"{BASE_URL}/v1/send").mock(
        return_value=httpx.Response(202, json={"id": "m", "status": "queued", "livemode": False})
    )
    requests = [TemplateSend(template="welcome", to=f"u{i}@example.com") for i in range(3)]
    client.send_batch(requests, idempotency_key="base", concurrency=2)

    keys = {call.request.headers["idempotency-key"] for call in route.calls}
    assert keys == {"base-0", "base-1", "base-2"}


@respx.mock
def test_batch_empty(client):
    assert client.send_batch([]) == []


@respx.mock
async def test_batch_async(aclient):
    respx.post(f"{BASE_URL}/v1/send").mock(side_effect=_handler)
    requests = [
        TemplateSend(template="welcome", to="ok@example.com"),
        TemplateSend(template="welcome", to="bad@example.com"),
    ]
    results = await aclient.send_batch(requests, concurrency=2)
    assert [r.index for r in results] == [0, 1]
    assert results[0].ok
    assert isinstance(results[1].error, ValidationError)
