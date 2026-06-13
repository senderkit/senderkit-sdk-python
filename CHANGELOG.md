# Changelog

## 0.1.0 (2026-06-13)

Initial release of the hand-written SenderKit Python SDK (replacing the earlier
Speakeasy-generated client).

- Sync (`SenderKit`) and async (`AsyncSenderKit`) clients over `httpx`.
- `send`, `send_raw` (email/SMS/push/web-push), and concurrent `send_batch`.
- `messages` (list/iter/get/cancel) and `templates` (list/get/render) resources.
- Idempotency keys by default; automatic retries with backoff honoring `Retry-After`.
- Typed error hierarchy (`SenderKitError` → `APIError` subclasses, `TimeoutError`,
  `NetworkError`, `SignatureVerificationError`).
- `WebhookVerifier` for HMAC-SHA256 signature verification.
- Framework integrations: Django (email backend, client, webhook view), FastAPI
  (dependencies), Flask (extension), Celery (send task).

### Not yet included

- SSE streaming client for `messages.list(tail=1)` (the raw parameter is available).
- An `mcp` submodule (present in the TypeScript SDK).
