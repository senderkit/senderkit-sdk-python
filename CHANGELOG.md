# Changelog

## [0.2.0](https://github.com/senderkit/senderkit-sdk-python/compare/v0.1.0...v0.2.0) (2026-07-08)


### Features

* **messages:** add openedAt/clickedAt engagement fields to Message ([577bdba](https://github.com/senderkit/senderkit-sdk-python/commit/577bdbac4e22e93815ae810a696e1ad4c7557bad))
* **messages:** add openedAt/clickedAt engagement fields to Message ([6b9cc30](https://github.com/senderkit/senderkit-sdk-python/commit/6b9cc3076ae3b1018a67a760d6e1ee3e9afa8489))
* **send:** per-send from/fromName email overrides ([838f0f1](https://github.com/senderkit/senderkit-sdk-python/commit/838f0f1957069360e635fd15a6b019b12447f716))
* **send:** per-send from/fromName email overrides on template and raw sends ([d493c4a](https://github.com/senderkit/senderkit-sdk-python/commit/d493c4ad8e308bfc36fb7eb5f73e74b986c18502))

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
