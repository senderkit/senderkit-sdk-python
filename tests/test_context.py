import httpx
import respx

from tests.helpers import BASE_URL


@respx.mock
def test_context(client):
    respx.get(f"{BASE_URL}/v1/context").mock(
        return_value=httpx.Response(
            200,
            json={
                "workspace": {"id": "ws_1", "slug": "acme", "name": "Acme"},
                "mode": "test",
            },
        )
    )
    ctx = client.context()
    assert ctx.mode == "test"
    assert ctx.workspace.id == "ws_1"
    assert ctx.workspace.slug == "acme"
    assert ctx.workspace.name == "Acme"


@respx.mock
async def test_context_async(aclient):
    respx.get(f"{BASE_URL}/v1/context").mock(
        return_value=httpx.Response(
            200,
            json={"workspace": {"id": "ws_1", "slug": "acme", "name": "Acme"}, "mode": "live"},
        )
    )
    ctx = await aclient.context()
    assert ctx.mode == "live"
