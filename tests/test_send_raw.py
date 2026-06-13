import respx

from senderkit import EmailContent, PushContent, SmsContent, WebPushContent
from tests.helpers import BASE_URL, json_response, request_body

QUEUED = {"id": "msg_1", "status": "queued", "livemode": False}


@respx.mock
def test_send_raw_email_infers_channel(client):
    route = respx.post(f"{BASE_URL}/v1/send").mock(
        return_value=json_response(202, QUEUED)
    )
    client.send_raw(
        "user@example.com",
        EmailContent(subject="Hi", html="<p>Hi {{name}}</p>", text="Hi"),
        interpolate=True,
        vars={"name": "Ada"},
    )
    body = request_body(route.calls.last.request)
    assert body["channel"] == "email"
    assert body["to"] == "user@example.com"
    assert body["interpolate"] is True
    assert body["content"] == {"subject": "Hi", "html": "<p>Hi {{name}}</p>", "text": "Hi"}
    assert body["vars"] == {"name": "Ada"}


@respx.mock
def test_send_raw_sms(client):
    route = respx.post(f"{BASE_URL}/v1/send").mock(
        return_value=json_response(202, QUEUED)
    )
    client.send_raw("+15555550123", SmsContent(body="Your code is 123456"))
    body = request_body(route.calls.last.request)
    assert body["channel"] == "sms"
    assert body["content"] == {"body": "Your code is 123456"}


@respx.mock
def test_send_raw_push(client):
    route = respx.post(f"{BASE_URL}/v1/send").mock(
        return_value=json_response(202, QUEUED)
    )
    client.send_raw("device-token", PushContent(title="T", body="B", badge=2))
    body = request_body(route.calls.last.request)
    assert body["channel"] == "push"
    assert body["content"] == {"title": "T", "body": "B", "badge": 2}


@respx.mock
def test_send_raw_web_push(client):
    route = respx.post(f"{BASE_URL}/v1/send").mock(
        return_value=json_response(202, QUEUED)
    )
    client.send_raw(
        "subscription",
        WebPushContent(title="T", body="B", click_url="https://x.test/y"),
        from_="sender@example.com",
    )
    body = request_body(route.calls.last.request)
    assert body["channel"] == "web-push"
    assert body["from"] == "sender@example.com"
    assert body["content"] == {"title": "T", "body": "B", "clickUrl": "https://x.test/y"}
