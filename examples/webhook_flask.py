"""Flask app exposing a send endpoint and a verified webhook receiver.

Run:
    pip install "senderkit[flask]"
    SENDERKIT_API_KEY=sk_test_... SENDERKIT_WEBHOOK_SECRET=whsec_... \
        flask --app examples/webhook_flask.py run
"""

import os

from flask import Flask, request

from senderkit.integrations.flask import SenderKitFlask

app = Flask(__name__)
app.config["SENDERKIT_API_KEY"] = os.environ["SENDERKIT_API_KEY"]
app.config["SENDERKIT_WEBHOOK_SECRET"] = os.environ.get("SENDERKIT_WEBHOOK_SECRET")
senderkit = SenderKitFlask(app)


@app.post("/welcome")
def welcome():
    result = senderkit.client.send("welcome", "user@example.com", vars={"name": "Ada"})
    return {"id": result.id, "status": result.status}


@app.post("/webhooks/senderkit")
def webhook():
    event = senderkit.verify_webhook(request)  # aborts 400 on a bad signature
    print("received:", event.type, event.payload)
    return "", 204
