"""Celery integration: a retryable background send task.

    from celery import Celery
    from senderkit import SenderKit
    from senderkit.integrations.celery import make_send_task

    celery_app = Celery("app", broker="redis://localhost:6379/0")
    send_email = make_send_task(celery_app, lambda: SenderKit(api_key="sk_..."))

    send_email.delay("welcome", "user@example.com", vars={"name": "Ada"})

The task calls ``client.send(template, to, **kwargs)`` and returns the result as a
dict (JSON-serializable for result backends). Transient failures — rate limits,
network errors, timeouts — are retried by Celery with exponential backoff, on top
of the SDK's own in-request retries for 5xx responses.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, Tuple, Type

from ..client import SenderKit
from ..errors import NetworkError, RateLimitError, SenderKitError, TimeoutError

# Transient errors worth retrying at the task level. (5xx is already retried inside
# the SDK, so a surfaced APIError is treated as terminal here.)
TRANSIENT_ERRORS: Tuple[Type[SenderKitError], ...] = (
    RateLimitError,
    NetworkError,
    TimeoutError,
)


def make_send_task(
    celery_app: Any,
    client_factory: Callable[[], SenderKit],
    *,
    name: str = "senderkit.send",
    max_retries: int = 3,
) -> Any:
    """Register and return a ``send(template, to, **kwargs)`` Celery task."""

    @celery_app.task(
        bind=True,
        name=name,
        max_retries=max_retries,
        autoretry_for=TRANSIENT_ERRORS,
        retry_backoff=True,
        retry_jitter=True,
    )
    def send_task(self: Any, template: str, to: str, **kwargs: Any) -> Dict[str, Any]:
        client = client_factory()
        result = client.send(template, to, **kwargs)
        return {"id": result.id, "status": result.status, "livemode": result.livemode}

    return send_task
