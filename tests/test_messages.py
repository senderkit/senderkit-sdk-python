import httpx
import pytest
import respx

from senderkit.errors import ConflictError
from tests.helpers import BASE_URL


def _msg(public_id: str, status: str = "delivered") -> dict:
    return {
        "id": "uuid-" + public_id,
        "publicId": public_id,
        "status": status,
        "channel": "email",
        "templateSlug": "welcome",
        "recipient": "user@example.com",
        "createdAt": "2026-01-01T00:00:00Z",
    }


@respx.mock
def test_list_with_filters_builds_query(client):
    route = respx.get(f"{BASE_URL}/v1/messages").mock(
        return_value=httpx.Response(200, json={"data": [_msg("msg_1")], "nextCursor": None})
    )
    page = client.messages.list(
        limit=10,
        status="delivered",
        channel="email",
        template="welcome",
        metadata={"userId": "usr_123"},
    )
    assert len(page.data) == 1
    assert page.data[0].public_id == "msg_1"
    assert page.next_cursor is None

    params = route.calls.last.request.url.params
    assert params["limit"] == "10"
    assert params["status"] == "delivered"
    assert params["channel"] == "email"
    assert params["template"] == "welcome"
    assert params["metadata[userId]"] == "usr_123"


@respx.mock
def test_iter_paginates(client):
    respx.get(f"{BASE_URL}/v1/messages").mock(
        side_effect=[
            httpx.Response(200, json={"data": [_msg("a"), _msg("b")], "nextCursor": "c2"}),
            httpx.Response(200, json={"data": [_msg("c")], "nextCursor": None}),
        ]
    )
    ids = [m.public_id for m in client.messages.iter(template="welcome")]
    assert ids == ["a", "b", "c"]


@respx.mock
def test_get_message(client):
    respx.get(f"{BASE_URL}/v1/messages/msg_1").mock(
        return_value=httpx.Response(200, json=_msg("msg_1"))
    )
    msg = client.messages.get("msg_1")
    assert msg.public_id == "msg_1"
    assert msg.raw["createdAt"] == "2026-01-01T00:00:00Z"  # forward-compat access


@respx.mock
def test_cancel_message(client):
    respx.delete(f"{BASE_URL}/v1/messages/msg_1").mock(
        return_value=httpx.Response(200, json={"id": "msg_1", "status": "canceled"})
    )
    result = client.messages.cancel("msg_1")
    assert (result.id, result.status) == ("msg_1", "canceled")


@respx.mock
def test_cancel_conflict(client, no_backoff):
    respx.delete(f"{BASE_URL}/v1/messages/msg_1").mock(
        return_value=httpx.Response(
            409, json={"error": {"code": "not_cancelable", "message": "already dispatched"}}
        )
    )
    with pytest.raises(ConflictError) as info:
        client.messages.cancel("msg_1")
    assert info.value.code == "not_cancelable"


@respx.mock
async def test_aiter_paginates(aclient):
    respx.get(f"{BASE_URL}/v1/messages").mock(
        side_effect=[
            httpx.Response(200, json={"data": [_msg("a")], "nextCursor": "c2"}),
            httpx.Response(200, json={"data": [_msg("b")], "nextCursor": None}),
        ]
    )
    ids = [m.public_id async for m in aclient.messages.aiter()]
    assert ids == ["a", "b"]
