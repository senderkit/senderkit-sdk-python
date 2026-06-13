# SenderKit Python SDK

[![PyPI version](https://img.shields.io/pypi/v/senderkit.svg)](https://pypi.org/project/senderkit/)
[![Python versions](https://img.shields.io/pypi/pyversions/senderkit.svg)](https://pypi.org/project/senderkit/)
[![CI](https://github.com/senderkit/senderkit-sdk-python/actions/workflows/ci.yml/badge.svg)](https://github.com/senderkit/senderkit-sdk-python/actions/workflows/ci.yml)
[![CodeQL](https://github.com/senderkit/senderkit-sdk-python/actions/workflows/codeql.yml/badge.svg)](https://github.com/senderkit/senderkit-sdk-python/actions/workflows/codeql.yml)
[![codecov](https://codecov.io/gh/senderkit/senderkit-sdk-python/branch/main/graph/badge.svg)](https://codecov.io/gh/senderkit/senderkit-sdk-python)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Checked with mypy](https://www.mypy-lang.org/static/mypy_badge.svg)](https://mypy-lang.org/)

The official Python client for [SenderKit](https://senderkit.com) — send transactional
**email, SMS, push, and web-push** through a single API, from one client.

- **Sync and async** — `SenderKit` and `AsyncSenderKit`, same methods.
- **Two ways to send** — render a stored template, or pass raw content inline.
- **Batch sends** that run concurrently and report per-recipient success/failure.
- **Safe by default** — every send carries an idempotency key, and transient
  failures (429 / 5xx / network) are retried automatically with backoff.
- **Typed throughout** (`py.typed`), with a clear exception hierarchy.
- **Webhook signature verification** and read access to messages and templates.
- One runtime dependency (`httpx`). Python 3.10+.

## Install

```bash
pip install senderkit
```

The framework integrations pull in their framework as an optional extra — install only what you need:

```bash
pip install "senderkit[django]"    # or: fastapi, flask, celery
pip install "senderkit[fastapi,celery]"
```

## Authentication

Create an API key in your [SenderKit dashboard](https://app.senderkit.com). Keys are
environment-scoped: `sk_test_…` keys send in test mode, `sk_live_…` keys send for real.
Keep the key out of source control — read it from the environment:

```python
import os
from senderkit import SenderKit

sk = SenderKit(api_key=os.environ["SENDERKIT_API_KEY"])
```

## Quick start

```python
import os
from senderkit import SenderKit

sk = SenderKit(api_key=os.environ["SENDERKIT_API_KEY"])

result = sk.send(
    "welcome",                  # template slug
    "user@example.com",         # recipient
    vars={"name": "Ada"},       # values interpolated into the template
    metadata={"user_id": "usr_123"},
)

print(result.id)        # "msg_..."
print(result.status)    # "queued"  (sends are dispatched asynchronously)
```

`send()` returns as soon as the message is accepted; `result.status` is `"queued"` for an
immediate send or `"scheduled"` when you pass `scheduled_at`. Track final delivery via
[webhooks](#webhooks) or [`sk.messages`](#messages).

### Async

`AsyncSenderKit` mirrors the sync client exactly — every method is the same, with `await`:

```python
import asyncio
from senderkit import AsyncSenderKit

async def main():
    async with AsyncSenderKit(api_key="sk_test_...") as sk:
        await sk.send("welcome", "user@example.com", vars={"name": "Ada"})

asyncio.run(main())
```

## Reusing the client

A `SenderKit` instance holds a pooled HTTP connection and is safe to share. In a
long-running app, **create it once at startup and reuse it** rather than per request:

```python
# module-level singleton
sk = SenderKit(api_key=os.environ["SENDERKIT_API_KEY"])
```

Call `sk.close()` (or `await sk.aclose()`) on shutdown. The `with` / `async with` form
shown above is convenient for scripts and one-off tasks, where it closes the client for you.

## Client options

```python
SenderKit(
    api_key,                              # required
    base_url="https://api.senderkit.com", # override for self-hosted / staging
    timeout=30.0,                         # per-request timeout, in seconds
    max_retries=2,                        # retries for 429 / 5xx / network errors
    http_client=None,                     # bring your own httpx.Client for proxies/TLS/pooling
)
```

`sk.mode` reports `"test"` or `"live"`, derived from the key prefix.

## Sending

### From a template

```python
from datetime import datetime, timezone

sk.send(
    "order-shipped",
    "user@example.com",
    vars={"order": "#1234"},
    metadata={"order_id": "ord_1"},                      # arbitrary key/values for filtering & webhooks
    cc=["ops@example.com"],                              # email only
    scheduled_at=datetime(2026, 1, 1, 9, 0, tzinfo=timezone.utc),  # datetime or ISO-8601 string
    idempotency_key="order-1234-shipped",                # optional; see Idempotency below
)
```

### Raw content (no template)

Pass a content object — the channel is inferred from its type. Set `interpolate=True` to
substitute `vars` into `{{ ... }}` placeholders in the content.

```python
from senderkit import EmailContent, SmsContent, PushContent, WebPushContent

# Email — `html` is required; `text` is an optional plain-text fallback.
sk.send_raw(
    "user@example.com",
    EmailContent(subject="Your receipt", html="<p>Thanks, {{name}}.</p>", text="Thanks, {{name}}."),
    interpolate=True,
    vars={"name": "Ada"},
)

sk.send_raw("+15555550123", SmsContent(body="Your code is 123456"))
sk.send_raw(device_token, PushContent(title="Hi", body="You have 1 new message", badge=1))
sk.send_raw(subscription_json, WebPushContent(title="Back in stock", body="Tap to view",
                                              click_url="https://example.com/item"))
```

### Batch

Sends many messages concurrently (a thread pool for sync, `asyncio` for async). A failed
item becomes a `BatchResult(ok=False, error=...)` instead of aborting the batch, and
results stay in the same order as the input.

```python
from senderkit import TemplateSend

requests = [
    TemplateSend(template="welcome", to=f"user{i}@example.com", vars={"n": i})
    for i in range(100)
]

results = sk.send_batch(requests, concurrency=10, idempotency_key="welcome-2026-01")

for r in results:
    if r.ok:
        print(r.index, r.result.id)
    else:
        print(r.index, "failed:", r.error)
```

When you pass a base `idempotency_key`, each item gets `"{key}-{index}"`.

## Idempotency

Every `send` / `send_raw` automatically attaches an `Idempotency-Key` (a fresh UUID), so a
network retry — by the SDK or by your own code — never sends the same message twice. Pass
your own `idempotency_key=` to make a send retry-safe across process restarts (e.g. keyed
on an order ID).

## Error handling

All exceptions derive from `senderkit.errors.SenderKitError`. API errors carry `.status`,
`.code`, `.issues`, and `.request_id` (quote `request_id` in support tickets).

```python
from senderkit import errors

try:
    sk.send("welcome", "user@example.com")
except errors.ValidationError as e:
    print("invalid request:", e.code, e.issues)   # 400 / 422
except errors.AuthenticationError:
    print("missing or invalid API key")            # 401 / 403
except errors.RateLimitError as e:
    print("rate limited; retry after", e.retry_after, "seconds")  # 429
except errors.PaymentRequiredError:
    print("plan limit reached")                    # 402
except errors.SenderKitError as e:
    print("send failed:", e)                       # catch-all
```

The full hierarchy: `AuthenticationError`, `ValidationError`, `PaymentRequiredError`,
`ConflictError` (e.g. cancelling an already-sent message), and `RateLimitError` are
`APIError` subclasses; `TimeoutError`, `NetworkError`, and `SignatureVerificationError`
sit alongside it. Transient failures are retried before they ever reach you (see
`max_retries`), honoring any `Retry-After` header.

## Messages

```python
# One page (newest first). Filter by status, channel, template, or metadata.
page = sk.messages.list(status="delivered", channel="email", limit=50,
                        metadata={"user_id": "usr_123"})
for m in page.data:
    print(m.public_id, m.status)
print(page.next_cursor)   # pass as cursor= for the next page, or None when done

# Or let the SDK follow the cursor for you:
for m in sk.messages.iter(template="welcome"):
    print(m.public_id, m.status)

msg = sk.messages.get("msg_123")
sk.messages.cancel("msg_123")   # only while still "scheduled" or "queued"
```

Every `Message` keeps the full API response in `m.raw`, so fields not yet surfaced as typed
attributes are still accessible.

## Templates

```python
for t in sk.templates.list():
    print(t.slug, t.channel)

detail = sk.templates.get("welcome")
print(detail.current_version.variables)

# Preview without sending; `missing` lists variables you didn't provide.
rendered = sk.templates.render("welcome", {"name": "Ada"})
print(rendered.output, rendered.missing)
```

## Webhooks

SenderKit signs each webhook with an HMAC over the raw request body. Verify it against the
`X-SenderKit-Signature` header **before** parsing — using your endpoint's signing secret
(`whsec_…`), not your API key:

```python
from senderkit import WebhookVerifier
from senderkit.errors import SignatureVerificationError

verifier = WebhookVerifier(secret=os.environ["SENDERKIT_WEBHOOK_SECRET"])

# In your handler — pass the RAW (undecoded) request body:
try:
    event = verifier.verify(raw_body, signature_header)
except SignatureVerificationError:
    return  # respond 400 and stop

print(event.type, event.payload)   # e.g. "message.delivered", {...}
```

The framework integrations below wire this up for you.

## Framework integrations

Each integration is importable once its extra is installed. See [`examples/`](examples) for
complete, runnable apps.

### Django

Route `django.core.mail` through SenderKit with a drop-in backend, and verify webhooks with
a view decorator:

```python
# settings.py
EMAIL_BACKEND = "senderkit.integrations.django.EmailBackend"
SENDERKIT = {
    "API_KEY": os.environ["SENDERKIT_API_KEY"],
    "WEBHOOK_SECRET": os.environ.get("SENDERKIT_WEBHOOK_SECRET"),
}
```

```python
from django.http import HttpResponse
from senderkit.integrations.django import get_client, senderkit_webhook

# A configured client, anywhere:
get_client().send("welcome", "user@example.com", vars={"name": "Ada"})

@senderkit_webhook                      # verifies the signature, then calls your view
def senderkit_events(request, event):
    print(event.type, event.payload)
    return HttpResponse(status=204)
```

### FastAPI

```python
from fastapi import Depends, FastAPI
from senderkit import AsyncSenderKit, WebhookEvent
from senderkit.integrations.fastapi import get_senderkit, webhook_verifier

app = FastAPI()
verify = webhook_verifier()             # secret from SENDERKIT_WEBHOOK_SECRET

@app.post("/welcome")
async def welcome(sk: AsyncSenderKit = Depends(get_senderkit)):
    await sk.send("welcome", "user@example.com")

@app.post("/webhooks/senderkit")
async def hook(event: WebhookEvent = Depends(verify)):
    return {"type": event.type}
```

`get_senderkit` reads `SENDERKIT_API_KEY` (and optional `SENDERKIT_BASE_URL` /
`SENDERKIT_TIMEOUT` / `SENDERKIT_MAX_RETRIES`) from the environment.

### Flask

```python
from flask import Flask, request
from senderkit.integrations.flask import SenderKitFlask

app = Flask(__name__)
app.config["SENDERKIT_API_KEY"] = os.environ["SENDERKIT_API_KEY"]
app.config["SENDERKIT_WEBHOOK_SECRET"] = os.environ.get("SENDERKIT_WEBHOOK_SECRET")
senderkit = SenderKitFlask(app)         # or SenderKitFlask().init_app(app)

@app.post("/welcome")
def welcome():
    senderkit.client.send("welcome", "user@example.com")
    return "", 204

@app.post("/webhooks/senderkit")
def hook():
    event = senderkit.verify_webhook(request)   # aborts 400 on a bad signature
    return {"type": event.type}
```

### Celery

`make_send_task` registers a retryable background-send task. Rate limits, network errors,
and timeouts are retried with exponential backoff:

```python
from celery import Celery
from senderkit import SenderKit
from senderkit.integrations.celery import make_send_task

celery_app = Celery("app", broker="redis://localhost:6379/0")
send_email = make_send_task(celery_app, lambda: SenderKit(api_key=os.environ["SENDERKIT_API_KEY"]))

send_email.delay("welcome", "user@example.com", vars={"name": "Ada"})
```

## License

MIT
