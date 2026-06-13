"""Exception hierarchy for the SenderKit SDK.

Mirrors the TypeScript and PHP SDKs: a single ``SenderKitError`` base, an
``APIError`` for non-2xx responses (with status-specific subclasses), plus
transport-level ``TimeoutError`` / ``NetworkError`` and a webhook
``SignatureVerificationError``. Catch the base ``SenderKitError`` to handle
everything the SDK can raise, or a specific subclass for granular handling.
"""

from __future__ import annotations

from typing import Any, Optional


class SenderKitError(Exception):
    """Base class for every error raised by the SDK."""


class APIError(SenderKitError):
    """The API returned a non-2xx response.

    ``status`` is the HTTP status code, ``code`` the machine-readable error code
    from the response body (e.g. ``invalid_request``), ``issues`` any structured
    validation detail, and ``request_id`` the ``x-request-id`` header for support.
    """

    def __init__(
        self,
        message: str,
        *,
        status: int,
        code: Optional[str] = None,
        issues: Any = None,
        request_id: Optional[str] = None,
    ) -> None:
        super().__init__(message)
        self.status = status
        self.code = code
        self.issues = issues
        self.request_id = request_id


class AuthenticationError(APIError):
    """401/403 — the API key is missing, invalid, or revoked."""


class ValidationError(APIError):
    """400/422 — the request was malformed or failed validation."""


class PaymentRequiredError(APIError):
    """402 — a plan limit was reached (e.g. ``message_limit_reached``)."""


class ConflictError(APIError):
    """409 — the resource is in a state that disallows the action.

    Raised by ``messages.cancel`` when a message has already been dispatched
    (``not_cancelable``); the message's freshly observed status is in ``code``/message.
    """


class RateLimitError(APIError):
    """429 — too many requests. ``retry_after`` is the server's hint, in seconds."""

    def __init__(
        self,
        message: str,
        *,
        status: int = 429,
        code: Optional[str] = None,
        issues: Any = None,
        request_id: Optional[str] = None,
        retry_after: Optional[float] = None,
    ) -> None:
        super().__init__(
            message, status=status, code=code, issues=issues, request_id=request_id
        )
        self.retry_after = retry_after


class TimeoutError(SenderKitError):
    """The request exceeded the configured timeout (shadows builtins.TimeoutError)."""


class NetworkError(SenderKitError):
    """A transport-level failure occurred before a response was received."""


class SignatureVerificationError(SenderKitError):
    """A webhook payload failed signature verification."""
