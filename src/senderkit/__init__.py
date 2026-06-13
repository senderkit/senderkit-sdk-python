"""SenderKit Python SDK.

    from senderkit import SenderKit

    with SenderKit(api_key="sk_test_...") as sk:
        sk.send("welcome", "user@example.com", vars={"name": "Ada"})

See :class:`SenderKit` / :class:`AsyncSenderKit` for the client, ``senderkit.errors``
for the exception hierarchy, and :class:`WebhookVerifier` for inbound webhooks.
"""

from __future__ import annotations

from . import errors
from ._version import VERSION
from .client import AsyncSenderKit, SenderKit
from .errors import (
    APIError,
    AuthenticationError,
    ConflictError,
    NetworkError,
    PaymentRequiredError,
    RateLimitError,
    SenderKitError,
    SignatureVerificationError,
    TimeoutError,
    ValidationError,
)
from .models import (
    Attachment,
    BatchResult,
    Channel,
    Context,
    EmailContent,
    Message,
    MessageList,
    PushContent,
    RawSend,
    RenderResult,
    SendResult,
    SmsContent,
    TemplateDetail,
    TemplateSend,
    TemplateSummary,
    TemplateVariable,
    TemplateVersion,
    WebPushContent,
    Workspace,
)
from .webhooks import WebhookEvent, WebhookVerifier

__version__ = VERSION

__all__ = [
    "VERSION",
    "__version__",
    "SenderKit",
    "AsyncSenderKit",
    "errors",
    # Errors
    "SenderKitError",
    "APIError",
    "AuthenticationError",
    "ValidationError",
    "PaymentRequiredError",
    "ConflictError",
    "RateLimitError",
    "TimeoutError",
    "NetworkError",
    "SignatureVerificationError",
    # Requests
    "TemplateSend",
    "RawSend",
    "EmailContent",
    "SmsContent",
    "PushContent",
    "WebPushContent",
    "Attachment",
    "Channel",
    # Responses
    "SendResult",
    "BatchResult",
    "Message",
    "MessageList",
    "TemplateSummary",
    "TemplateDetail",
    "TemplateVersion",
    "TemplateVariable",
    "RenderResult",
    "Context",
    "Workspace",
    # Webhooks
    "WebhookVerifier",
    "WebhookEvent",
]
