"""A decorator that verifies a SenderKit webhook before calling your view.

    from senderkit.integrations.django import senderkit_webhook

    @senderkit_webhook
    def handle(request, event):
        if event.type == "message.delivered":
            ...
        return HttpResponse(status=204)

The secret comes from ``SENDERKIT['WEBHOOK_SECRET']`` unless passed explicitly.
A missing/invalid/stale signature yields an HTTP 400 before your view runs.
"""

from __future__ import annotations

from functools import wraps
from typing import Any, Callable, Optional

from ...errors import SignatureVerificationError
from ...webhooks import DEFAULT_TOLERANCE_SECONDS, WebhookVerifier
from .client import get_config


def senderkit_webhook(
    view: Optional[Callable[..., Any]] = None,
    *,
    secret: Optional[str] = None,
    tolerance: int = DEFAULT_TOLERANCE_SECONDS,
) -> Callable[..., Any]:
    """Wrap a view ``(request, event, *args, **kwargs)``; usable bare or with args."""

    def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        from django.http import HttpResponseBadRequest
        from django.views.decorators.csrf import csrf_exempt

        @csrf_exempt
        @wraps(fn)
        def wrapper(request: Any, *args: Any, **kwargs: Any) -> Any:
            signing_secret = secret or get_config().get("WEBHOOK_SECRET")
            try:
                event = WebhookVerifier(signing_secret).verify(
                    request.body,
                    request.headers.get("X-SenderKit-Signature", ""),
                    tolerance=tolerance,
                    event_type=request.headers.get("X-SenderKit-Event"),
                    delivery_id=request.headers.get("X-SenderKit-Delivery"),
                )
            except SignatureVerificationError as exc:
                return HttpResponseBadRequest(str(exc))
            return fn(request, event, *args, **kwargs)

        return wrapper

    return decorator(view) if view is not None else decorator
