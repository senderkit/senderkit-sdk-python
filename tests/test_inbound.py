import httpx
import respx

from tests.helpers import BASE_URL, request_body


@respx.mock
def test_list_inbound_addresses(client):
    respx.get(f"{BASE_URL}/v1/inbound/addresses").mock(
        return_value=httpx.Response(
            200,
            json={
                "addresses": [
                    {
                        "id": "inb_1",
                        "address": "support@acme.in.senderkit.email",
                        "description": "Support intake",
                        "forwardTo": None,
                        "active": True,
                        "livemode": False,
                        "createdAt": "2026-05-10T00:00:00Z",
                    }
                ]
            },
        )
    )
    addresses = client.inbound.addresses.list()
    assert len(addresses) == 1
    assert addresses[0].id == "inb_1"
    assert addresses[0].address == "support@acme.in.senderkit.email"


@respx.mock
def test_create_inbound_address_sends_only_provided_fields(client):
    route = respx.post(f"{BASE_URL}/v1/inbound/addresses").mock(
        return_value=httpx.Response(
            201,
            json={
                "id": "inb_2",
                "address": "support@acme.in.senderkit.email",
                "description": None,
                "forwardTo": None,
                "active": True,
                "livemode": False,
                "createdAt": "2026-05-10T00:00:00Z",
            },
        )
    )
    created = client.inbound.addresses.create(local_part="support")
    assert created.id == "inb_2"
    assert request_body(route.calls.last.request) == {"localPart": "support"}


@respx.mock
def test_delete_inbound_address(client):
    respx.delete(f"{BASE_URL}/v1/inbound/addresses/inb_1").mock(
        return_value=httpx.Response(200, json={"deleted": True})
    )
    assert client.inbound.addresses.delete("inb_1") is True


@respx.mock
def test_list_inbound_messages_with_filters(client):
    route = respx.get(f"{BASE_URL}/v1/inbound/messages").mock(
        return_value=httpx.Response(
            200,
            json={
                "messages": [
                    {
                        "id": "rcv_1",
                        "status": "received",
                        "from": "sender@example.com",
                        "subject": "Hello",
                        "plusTag": None,
                        "sizeBytes": 42,
                        "receivedAt": "2026-05-10T00:00:00Z",
                    }
                ]
            },
        )
    )
    messages = client.inbound.messages.list(limit=10, address="inb_1")
    assert len(messages) == 1
    assert messages[0].id == "rcv_1"
    assert messages[0].from_ == "sender@example.com"
    params = dict(route.calls.last.request.url.params)
    assert params["limit"] == "10"
    assert params["address"] == "inb_1"


@respx.mock
def test_get_inbound_message(client):
    respx.get(f"{BASE_URL}/v1/inbound/messages/rcv_1").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": "rcv_1",
                "status": "received",
                "channel": "email",
                "address": "support@acme.in.senderkit.email",
                "subject": "Hello",
                "text": "Hi there",
                "html": None,
                "strippedReply": "Hi there",
                "sizeBytes": 42,
                "receivedAt": "2026-05-10T00:00:00Z",
                "rawUrl": "https://api.test/v1/inbound/messages/rcv_1/raw",
                "attachments": [
                    {
                        "index": 0,
                        "filename": "invoice.pdf",
                        "contentType": "application/pdf",
                        "size": 1024,
                        "url": "https://api.test/v1/inbound/messages/rcv_1/attachments/0",
                    }
                ],
            },
        )
    )
    msg = client.inbound.messages.get("rcv_1")
    assert msg.subject == "Hello"
    assert msg.text == "Hi there"
    assert len(msg.attachments) == 1
    assert msg.attachments[0].filename == "invoice.pdf"


@respx.mock
def test_get_inbound_message_raw_returns_bytes(client):
    respx.get(f"{BASE_URL}/v1/inbound/messages/rcv_1/raw").mock(
        return_value=httpx.Response(
            200,
            content=b"From: a@b.com\r\nSubject: Hi\r\n\r\nBody",
            headers={"content-type": "message/rfc822"},
        )
    )
    raw = client.inbound.messages.raw("rcv_1")
    assert raw.content_type == "message/rfc822"
    assert b"Subject: Hi" in raw.content


@respx.mock
def test_get_inbound_attachment_parses_filename(client):
    respx.get(f"{BASE_URL}/v1/inbound/messages/rcv_1/attachments/0").mock(
        return_value=httpx.Response(
            200,
            content=b"PDFBYTES",
            headers={
                "content-type": "application/pdf",
                "content-disposition": 'attachment; filename="invoice.pdf"',
            },
        )
    )
    att = client.inbound.messages.attachment("rcv_1", 0)
    assert att.content == b"PDFBYTES"
    assert att.content_type == "application/pdf"
    assert att.filename == "invoice.pdf"


@respx.mock
def test_create_inbound_address_with_domain_and_livemode(client):
    route = respx.post(f"{BASE_URL}/v1/inbound/addresses").mock(
        return_value=httpx.Response(
            201,
            json={
                "id": "inb_3",
                "address": "*@inbound.acme.com",
                "description": None,
                "forwardTo": None,
                "active": True,
                "livemode": False,
                "createdAt": "2026-05-10T00:00:00Z",
            },
        )
    )
    created = client.inbound.addresses.create(
        local_part="*",
        domain_id="11111111-1111-1111-1111-111111111111",
        livemode=False,
    )
    assert created.id == "inb_3"
    assert request_body(route.calls.last.request) == {
        "localPart": "*",
        "domainId": "11111111-1111-1111-1111-111111111111",
        "livemode": False,
    }


@respx.mock
def test_list_inbound_domains(client):
    respx.get(f"{BASE_URL}/v1/inbound/domains").mock(
        return_value=httpx.Response(
            200,
            json={
                "domains": [
                    {
                        "id": "d1",
                        "domain": "acme.in.senderkit.email",
                        "kind": "shared",
                        "status": "verified",
                        "records": [],
                        "verifiedAt": "2026-05-10T00:00:00Z",
                        "createdAt": "2026-05-10T00:00:00Z",
                    },
                    {
                        "id": "d2",
                        "domain": "inbound.acme.com",
                        "kind": "custom",
                        "status": "pending",
                        "records": [
                            {
                                "type": "MX",
                                "name": "inbound.acme.com",
                                "value": "inbound-smtp.senderkit.email",
                                "priority": 10,
                                "purpose": "receiving",
                            }
                        ],
                        "verifiedAt": None,
                        "createdAt": "2026-05-10T00:00:00Z",
                    },
                ]
            },
        )
    )
    domains = client.inbound.domains.list()
    assert len(domains) == 2
    assert domains[1].domain == "inbound.acme.com"
    assert domains[1].records[0].type == "MX"
    assert domains[1].records[0].priority == 10


@respx.mock
def test_create_inbound_domain(client):
    route = respx.post(f"{BASE_URL}/v1/inbound/domains").mock(
        return_value=httpx.Response(
            201,
            json={
                "id": "d3",
                "domain": "inbound.acme.com",
                "kind": "custom",
                "status": "pending",
                "records": [],
                "verifiedAt": None,
                "createdAt": "2026-05-10T00:00:00Z",
            },
        )
    )
    created = client.inbound.domains.create("inbound.acme.com", acknowledge_existing_mx=True)
    assert created.id == "d3"
    assert request_body(route.calls.last.request) == {
        "domain": "inbound.acme.com",
        "acknowledgeExistingMx": True,
    }


def test_create_inbound_domain_requires_domain(client):
    import pytest

    with pytest.raises(ValueError):
        client.inbound.domains.create("")


@respx.mock
def test_delete_inbound_domain(client):
    respx.delete(f"{BASE_URL}/v1/inbound/domains/d3").mock(
        return_value=httpx.Response(200, json={"deleted": True})
    )
    assert client.inbound.domains.delete("d3") is True


@respx.mock
async def test_create_inbound_address_with_domain_and_livemode_async(aclient):
    route = respx.post(f"{BASE_URL}/v1/inbound/addresses").mock(
        return_value=httpx.Response(
            201,
            json={
                "id": "inb_3",
                "address": "*@inbound.acme.com",
                "description": None,
                "forwardTo": None,
                "active": True,
                "livemode": False,
                "createdAt": "2026-05-10T00:00:00Z",
            },
        )
    )
    created = await aclient.inbound.addresses.create(
        local_part="*",
        domain_id="11111111-1111-1111-1111-111111111111",
        livemode=False,
    )
    assert created.id == "inb_3"
    assert request_body(route.calls.last.request) == {
        "localPart": "*",
        "domainId": "11111111-1111-1111-1111-111111111111",
        "livemode": False,
    }


@respx.mock
async def test_list_inbound_domains_async(aclient):
    respx.get(f"{BASE_URL}/v1/inbound/domains").mock(
        return_value=httpx.Response(
            200,
            json={
                "domains": [
                    {
                        "id": "d2",
                        "domain": "inbound.acme.com",
                        "kind": "custom",
                        "status": "pending",
                        "records": [
                            {
                                "type": "MX",
                                "name": "inbound.acme.com",
                                "value": "inbound-smtp.senderkit.email",
                                "priority": 10,
                                "purpose": "receiving",
                            }
                        ],
                        "verifiedAt": None,
                        "createdAt": "2026-05-10T00:00:00Z",
                    }
                ]
            },
        )
    )
    domains = await aclient.inbound.domains.list()
    assert len(domains) == 1
    assert domains[0].domain == "inbound.acme.com"
    assert domains[0].records[0].priority == 10


@respx.mock
async def test_create_inbound_domain_async(aclient):
    route = respx.post(f"{BASE_URL}/v1/inbound/domains").mock(
        return_value=httpx.Response(
            201,
            json={
                "id": "d3",
                "domain": "inbound.acme.com",
                "kind": "custom",
                "status": "pending",
                "records": [],
                "verifiedAt": None,
                "createdAt": "2026-05-10T00:00:00Z",
            },
        )
    )
    created = await aclient.inbound.domains.create("inbound.acme.com", acknowledge_existing_mx=True)
    assert created.id == "d3"
    assert request_body(route.calls.last.request) == {
        "domain": "inbound.acme.com",
        "acknowledgeExistingMx": True,
    }


@respx.mock
async def test_delete_inbound_domain_async(aclient):
    respx.delete(f"{BASE_URL}/v1/inbound/domains/d3").mock(
        return_value=httpx.Response(200, json={"deleted": True})
    )
    assert await aclient.inbound.domains.delete("d3") is True


@respx.mock
async def test_async_inbound_addresses_full_surface(aclient):
    # create with every field (covers the create-body branches) ...
    create = respx.post(f"{BASE_URL}/v1/inbound/addresses").mock(
        return_value=httpx.Response(
            201,
            json={
                "id": "inb_9",
                "address": "support@acme.in.senderkit.email",
                "description": "Support",
                "forwardTo": "team@acme.com",
                "active": True,
                "livemode": True,
                "createdAt": "2026-05-10T00:00:00Z",
            },
        )
    )
    created = await aclient.inbound.addresses.create(
        local_part="support",
        description="Support",
        forward_to="team@acme.com",
        webhook_endpoint_id="22222222-2222-2222-2222-222222222222",
    )
    assert created.id == "inb_9"
    assert request_body(create.calls.last.request) == {
        "localPart": "support",
        "description": "Support",
        "forwardTo": "team@acme.com",
        "webhookEndpointId": "22222222-2222-2222-2222-222222222222",
    }

    # ... list ...
    respx.get(f"{BASE_URL}/v1/inbound/addresses").mock(
        return_value=httpx.Response(200, json={"addresses": [{"id": "inb_9", "address": "x@y.z"}]})
    )
    addrs = await aclient.inbound.addresses.list()
    assert addrs[0].id == "inb_9"

    # ... delete.
    respx.delete(f"{BASE_URL}/v1/inbound/addresses/inb_9").mock(
        return_value=httpx.Response(200, json={"deleted": True})
    )
    assert await aclient.inbound.addresses.delete("inb_9") is True


@respx.mock
async def test_async_inbound_messages_full_surface(aclient):
    # list with a datetime `before` cursor (exercises the ISO conversion) ...
    lst = respx.get(f"{BASE_URL}/v1/inbound/messages").mock(
        return_value=httpx.Response(
            200,
            json={"messages": [{"id": "rcv_1", "status": "received", "sizeBytes": 42}]},
        )
    )
    from datetime import datetime, timezone

    msgs = await aclient.inbound.messages.list(
        limit=10, before=datetime(2026, 5, 10, tzinfo=timezone.utc), address="inb_1"
    )
    assert msgs[0].id == "rcv_1"
    assert "before=2026-05-10" in str(lst.calls.last.request.url)

    # ... get ...
    respx.get(f"{BASE_URL}/v1/inbound/messages/rcv_1").mock(
        return_value=httpx.Response(
            200, json={"id": "rcv_1", "status": "received", "subject": "Hi"}
        )
    )
    msg = await aclient.inbound.messages.get("rcv_1")
    assert msg.subject == "Hi"

    # ... raw bytes ...
    respx.get(f"{BASE_URL}/v1/inbound/messages/rcv_1/raw").mock(
        return_value=httpx.Response(
            200, content=b"From: a@b\r\n\r\nBody", headers={"content-type": "message/rfc822"}
        )
    )
    raw = await aclient.inbound.messages.raw("rcv_1")
    assert raw.content_type == "message/rfc822"

    # ... attachment bytes (with a filename to parse).
    respx.get(f"{BASE_URL}/v1/inbound/messages/rcv_1/attachments/0").mock(
        return_value=httpx.Response(
            200,
            content=b"PDF",
            headers={
                "content-type": "application/pdf",
                "content-disposition": 'attachment; filename="invoice.pdf"',
            },
        )
    )
    att = await aclient.inbound.messages.attachment("rcv_1", 0)
    assert att.filename == "invoice.pdf"
