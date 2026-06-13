"""FastAPI integration for SenderKit.

Two helpers:

- ``get_senderkit`` — a dependency yielding a shared :class:`~senderkit.AsyncSenderKit`
  built from ``SENDERKIT_*`` environment variables.
- ``webhook_verifier(...)`` — builds a route dependency that verifies the request
  signature and returns the parsed :class:`~senderkit.WebhookEvent` (HTTP 400 on failure).

Example::

    from fastapi import Depends, FastAPI
    from senderkit import AsyncSenderKit, WebhookEvent
    from senderkit.integrations.fastapi import get_senderkit, webhook_verifier

    app = FastAPI()

    @app.post("/welcome")
    async def welcome(sk: AsyncSenderKit = Depends(get_senderkit)):
        await sk.send("welcome", "user@example.com")

    verify = webhook_verifier()  # secret from SENDERKIT_WEBHOOK_SECRET

    @app.post("/webhooks/senderkit")
    async def hook(event: WebhookEvent = Depends(verify)):
        return {"type": event.type}
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Awaitable, Callable, Optional

from fastapi import HTTPException, Request

from ..client import (
    DEFAULT_BASE_URL,
    DEFAULT_MAX_RETRIES,
    DEFAULT_TIMEOUT,
    AsyncSenderKit,
)
from ..errors import SignatureVerificationError
from ..webhooks import DEFAULT_TOLERANCE_SECONDS, WebhookEvent, WebhookVerifier


@lru_cache(maxsize=1)
def get_senderkit() -> AsyncSenderKit:
    """Return a cached :class:`~senderkit.AsyncSenderKit` from the environment.

    Reads ``SENDERKIT_API_KEY`` (required), ``SENDERKIT_BASE_URL``,
    ``SENDERKIT_TIMEOUT``, and ``SENDERKIT_MAX_RETRIES``.
    """
    api_key = os.environ.get("SENDERKIT_API_KEY")
    if not api_key:
        raise RuntimeError("SENDERKIT_API_KEY is not set.")
    return AsyncSenderKit(
        api_key=api_key,
        base_url=os.environ.get("SENDERKIT_BASE_URL", DEFAULT_BASE_URL),
        timeout=float(os.environ.get("SENDERKIT_TIMEOUT", DEFAULT_TIMEOUT)),
        max_retries=int(os.environ.get("SENDERKIT_MAX_RETRIES", DEFAULT_MAX_RETRIES)),
    )


def webhook_verifier(
    secret: Optional[str] = None,
    *,
    tolerance: int = DEFAULT_TOLERANCE_SECONDS,
) -> Callable[[Request], Awaitable[WebhookEvent]]:
    """Build a dependency that verifies the webhook signature on a request."""

    async def dependency(request: Request) -> WebhookEvent:
        signing_secret = secret or os.environ.get("SENDERKIT_WEBHOOK_SECRET")
        body = await request.body()
        try:
            return WebhookVerifier(signing_secret).verify(
                body,
                request.headers.get("x-senderkit-signature", ""),
                tolerance=tolerance,
                event_type=request.headers.get("x-senderkit-event"),
                delivery_id=request.headers.get("x-senderkit-delivery"),
            )
        except SignatureVerificationError as exc:
            raise HTTPException(status_code=400, detail=str(exc))

    return dependency
