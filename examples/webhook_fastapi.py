"""FastAPI app with an injected client and a verified webhook receiver.

Run:
    pip install "senderkit[fastapi]" uvicorn
    SENDERKIT_API_KEY=sk_test_... SENDERKIT_WEBHOOK_SECRET=whsec_... \
        uvicorn examples.webhook_fastapi:app
"""

from fastapi import Depends, FastAPI

from senderkit import AsyncSenderKit, WebhookEvent
from senderkit.integrations.fastapi import get_senderkit, webhook_verifier

app = FastAPI()
verify = webhook_verifier()  # secret from SENDERKIT_WEBHOOK_SECRET


@app.post("/welcome")
async def welcome(sk: AsyncSenderKit = Depends(get_senderkit)):  # noqa: B008
    result = await sk.send("welcome", "user@example.com", vars={"name": "Ada"})
    return {"id": result.id, "status": result.status}


@app.post("/webhooks/senderkit")
async def webhook(event: WebhookEvent = Depends(verify)):  # noqa: B008
    print("received:", event.type, event.payload)
    return {"ok": True}
