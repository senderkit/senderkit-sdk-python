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
