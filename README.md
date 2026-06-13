# SenderKit Python SDK

The official Python client for [SenderKit](https://senderkit.com) — send transactional
**email, SMS, push, and web-push** from one API. Hand-written to match the
[TypeScript](https://github.com/senderkit/senderkit-sdk) and
[PHP](https://github.com/senderkit/senderkit-sdk-php) SDKs: the same ergonomic surface,
error model, idempotency, and retry behavior, plus **sync + async** clients and drop-in
integrations for **Django, FastAPI, Flask, and Celery**.

- Sync (`SenderKit`) and async (`AsyncSenderKit`) clients over `httpx`
- Templated sends, raw sends (email/SMS/push/web-push), and concurrent batch sends
- Idempotency keys by default, automatic retries with backoff, typed errors
- Cursor pagination with auto-iterating helpers
- HMAC webhook signature verification
- One runtime dependency (`httpx`); typed (`py.typed`); Python 3.10+

## Install

```bash
pip install senderkit
# with framework integrations:
pip install "senderkit[django]"   # or fastapi / flask / celery
```

## Quick start

```python
from senderkit import SenderKit

with SenderKit(api_key="sk_test_...") as sk:
    result = sk.send(
        "welcome",                       # template slug
        "user@example.com",              # recipient
        vars={"name": "Ada"},
        metadata={"userId": "usr_123"},
    )
    print(result.id, result.status)      # msg_...  queued
```

Async is identical with `await`:

```python
import asyncio
from senderkit import AsyncSenderKit

async def main():
    async with AsyncSenderKit(api_key="sk_test_...") as sk:
        await sk.send("welcome", "user@example.com", vars={"name": "Ada"})

asyncio.run(main())
```

## Sending

### Templated send

```python
sk.send(
    "order-shipped", "user@example.com",
    vars={"order": "#1234"},
    metadata={"orderId": "ord_1"},
    scheduled_at=datetime(2026, 1, 1, 9, 0),   # str or datetime; omit to send now
    idempotency_key="order-1234-shipped",       # auto-generated UUID if omitted
)
```

### Raw send (inline content)

The channel is inferred from the content type.

```python
from senderkit import EmailContent, SmsContent, PushContent, WebPushContent

sk.send_raw("user@example.com", EmailContent(
    subject="Your receipt",
    html="<p>Thanks, {{name}}.</p>",
    text="Thanks, {{name}}.",
), interpolate=True, vars={"name": "Ada"})

sk.send_raw("+15555550123", SmsContent(body="Your code is 123456"))
sk.send_raw(device_token, PushContent(title="Hi", body="You have 1 new message", badge=1))
sk.send_raw(subscription_json, WebPushContent(title="Hi", body="Back in stock", click_url="https://..."))
```

### Batch send

Runs concurrently (thread pool for sync, `asyncio` for async). Per-item failures are
captured, not raised — results are positionally aligned with the input.

```python
from senderkit import TemplateSend

results = sk.send_batch(
    [TemplateSend(template="welcome", to=f"u{i}@example.com", vars={"n": i}) for i in range(100)],
    concurrency=10,
    idempotency_key="welcome-2026-01",   # each item gets "{key}-{index}"
)
for r in results:
    print(r.index, "ok" if r.ok else r.error)
```

## Live vs test mode

The API key prefix decides the environment. `sk.mode` is `"test"` for `sk_test_…` keys and
`"live"` otherwise.

## Idempotency

`send` / `send_raw` attach an `Idempotency-Key` automatically (a fresh UUID) so a retried
request never double-sends. Pass `idempotency_key=` to supply your own.

## Error handling

```python
from senderkit import errors

try:
    sk.send("welcome", "user@example.com")
except errors.ValidationError as e:
    print("bad request:", e.message if hasattr(e, "message") else e, e.issues)
except errors.AuthenticationError:
    print("check your API key")
except errors.RateLimitError as e:
    print("retry after", e.retry_after, "seconds")
except errors.PaymentRequiredError:
    print("plan limit reached")
except errors.TimeoutError:
    print("timed out")
except errors.NetworkError:
    print("network failure")
except errors.SenderKitError:
    print("something else went wrong")
```

`APIError` (and its subclasses) carry `.status`, `.code`, `.issues`, and `.request_id`.
Transient failures (429, 5xx, network) are retried automatically (`max_retries`, default 2)
with exponential backoff that honors `Retry-After`.

## Messages & templates

```python
page = sk.messages.list(status="delivered", channel="email", limit=50,
                        metadata={"userId": "usr_123"})
for m in sk.messages.iter(template="welcome"):   # auto-paginates
    print(m.public_id, m.status)

msg = sk.messages.get("msg_123")
sk.messages.cancel("msg_123")                    # scheduled/queued only

for t in sk.templates.list():
    print(t.slug, t.channel)
detail = sk.templates.get("welcome")
rendered = sk.templates.render("welcome", {"name": "Ada"})
print(rendered.output, rendered.missing)
```

## Webhooks

```python
from senderkit import WebhookVerifier
from senderkit.errors import SignatureVerificationError

verifier = WebhookVerifier(secret="whsec_...")
try:
    event = verifier.verify(raw_request_body, request.headers["X-SenderKit-Signature"])
    print(event.type, event.payload)
except SignatureVerificationError:
    ...  # reject the request (HTTP 400)
```

## Framework integrations

- **Django** — `senderkit.integrations.django`: a drop-in `EMAIL_BACKEND`, a configured
  `get_client()`, and a `senderkit_webhook` view decorator.
- **FastAPI** — `senderkit.integrations.fastapi`: a `get_senderkit` dependency and a
  `webhook_verifier(...)` route dependency.
- **Flask** — `senderkit.integrations.flask`: a `SenderKit` extension (`init_app`) and a
  `verify_webhook(request)` helper.
- **Celery** — `senderkit.integrations.celery`: `make_send_task(...)` for retryable
  background sends.

See [`examples/`](examples) for runnable snippets of each.

## Notes

- `timeout` is in **seconds** (httpx convention). The TS/PHP SDKs use milliseconds.
- Pass your own `httpx.Client` / `httpx.AsyncClient` via `http_client=` for proxies, TLS,
  or pooling control.

## License

MIT
