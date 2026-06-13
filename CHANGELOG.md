# Changelog

## 0.1.0 (2026-06-13)


### Features

* automate releases with release-please ([a8ccebd](https://github.com/senderkit/senderkit-sdk-python/commit/a8ccebd6ebef1a4a5ff04e5b52d3027a12899193))
* automate releases with release-please ([aec6d70](https://github.com/senderkit/senderkit-sdk-python/commit/aec6d700dc9c4cf8a7d42fa56c7ddbe4cb11c304))


### Bug Fixes

* bootstrap first release as 0.1.0 and fix release workflow ([46cf045](https://github.com/senderkit/senderkit-sdk-python/commit/46cf0450c11d71b58cf8ab710144c25e363800b3))
* bootstrap first release as 0.1.0 and fix release workflow ([94e679a](https://github.com/senderkit/senderkit-sdk-python/commit/94e679a798544ef86246f83ecdf2e5e3127ab2dc))

## 0.1.0

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
