"""Django email-backend and webhook-view tests.

Configures a minimal Django settings module in-process, then exercises the
EmailBackend through ``django.core.mail`` against a mocked SenderKit API.
"""

import hashlib
import hmac

import django
import httpx
import pytest
import respx
from django.conf import settings

from tests.helpers import BASE_URL

if not settings.configured:
    settings.configure(
        DEBUG=True,
        ALLOWED_HOSTS=["*"],
        EMAIL_BACKEND="senderkit.integrations.django.EmailBackend",
        SENDERKIT={
            "API_KEY": "sk_test_123",
            "BASE_URL": BASE_URL,
            "WEBHOOK_SECRET": "whsec_test",
        },
        ROOT_URLCONF=__name__,
    )
    django.setup()

urlpatterns: list = []

QUEUED = {"id": "msg_1", "status": "queued", "livemode": False}


@pytest.fixture(autouse=True)
def _reset_client():
    from senderkit.integrations.django import reset_client

    reset_client()
    yield
    reset_client()


@respx.mock
def test_send_mail_routes_through_senderkit():
    from django.core.mail import send_mail

    route = respx.post(f"{BASE_URL}/v1/send").mock(
        return_value=httpx.Response(202, json=QUEUED)
    )
    sent = send_mail(
        subject="Hi",
        message="Plain body",
        from_email="from@example.com",
        recipient_list=["a@example.com", "b@example.com"],
    )
    assert sent == 2  # one API call per recipient
    assert route.call_count == 2
    import json as _json

    body = _json.loads(route.calls[0].request.content)
    assert body["channel"] == "email"
    assert body["content"]["subject"] == "Hi"
    assert body["from"] == "from@example.com"


@respx.mock
def test_send_html_alternative():
    from django.core.mail import EmailMultiAlternatives

    route = respx.post(f"{BASE_URL}/v1/send").mock(
        return_value=httpx.Response(202, json=QUEUED)
    )
    msg = EmailMultiAlternatives(
        subject="Hi", body="text", from_email="f@example.com", to=["a@example.com"]
    )
    msg.attach_alternative("<p>html</p>", "text/html")
    msg.send()

    import json as _json

    body = _json.loads(route.calls.last.request.content)
    assert body["content"]["html"] == "<p>html</p>"
    assert body["content"]["text"] == "text"


def test_webhook_view_accepts_valid_signature():
    from django.test import RequestFactory

    from senderkit.integrations.django import senderkit_webhook

    def handler(request, event):
        from django.http import JsonResponse

        return JsonResponse({"type": event.type})

    body = b'{"hello": "world"}'
    ts = 1000
    digest = hmac.new(b"whsec_test", f"{ts}.".encode() + body, hashlib.sha256).hexdigest()
    request = RequestFactory().post(
        "/webhooks",
        data=body,
        content_type="application/json",
        HTTP_X_SENDERKIT_SIGNATURE=f"t={ts},v1={digest}",
        HTTP_X_SENDERKIT_EVENT="message.delivered",
    )
    # The verifier uses real time; widen tolerance so the fixed timestamp is in window.
    wrapped = senderkit_webhook(handler, tolerance=10**12)
    response = wrapped(request)
    assert response.status_code == 200
    assert b"message.delivered" in response.content


def test_webhook_view_rejects_bad_signature():
    from django.test import RequestFactory

    from senderkit.integrations.django import senderkit_webhook

    @senderkit_webhook
    def handler(request, event):  # pragma: no cover - should not run
        from django.http import HttpResponse

        return HttpResponse(status=204)

    request = RequestFactory().post(
        "/webhooks",
        data=b"{}",
        content_type="application/json",
        HTTP_X_SENDERKIT_SIGNATURE="t=1,v1=deadbeef",
    )
    response = handler(request)
    assert response.status_code == 400
