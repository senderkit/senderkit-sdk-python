import hashlib
import hmac

import httpx
import respx
from flask import Flask, request

from senderkit.integrations.flask import SenderKitFlask
from tests.helpers import BASE_URL


def _make_app() -> tuple[Flask, SenderKitFlask]:
    app = Flask(__name__)
    app.config["SENDERKIT_API_KEY"] = "sk_test_123"
    app.config["SENDERKIT_BASE_URL"] = BASE_URL
    app.config["SENDERKIT_WEBHOOK_SECRET"] = "whsec_test"
    ext = SenderKitFlask(app)

    @app.post("/send")
    def send():
        ext.client.send("welcome", "user@example.com")
        return "", 204

    @app.post("/webhooks")
    def hook():
        event = ext.verify_webhook(request, tolerance=10**12)
        return {"type": event.type}

    return app, ext


@respx.mock
def test_client_sends():
    app, _ = _make_app()
    queued = {"id": "msg_1", "status": "queued", "livemode": False}
    respx.post(f"{BASE_URL}/v1/send").mock(return_value=httpx.Response(202, json=queued))
    response = app.test_client().post("/send")
    assert response.status_code == 204


def test_webhook_valid():
    app, _ = _make_app()
    body = b'{"x": 1}'
    digest = hmac.new(b"whsec_test", b"1000." + body, hashlib.sha256).hexdigest()
    response = app.test_client().post(
        "/webhooks",
        data=body,
        content_type="application/json",
        headers={"X-SenderKit-Signature": f"t=1000,v1={digest}", "X-SenderKit-Event": "ping"},
    )
    assert response.status_code == 200
    assert response.get_json() == {"type": "ping"}


def test_webhook_bad_signature():
    app, _ = _make_app()
    response = app.test_client().post(
        "/webhooks",
        data=b"{}",
        content_type="application/json",
        headers={"X-SenderKit-Signature": "t=1,v1=bad"},
    )
    assert response.status_code == 400
