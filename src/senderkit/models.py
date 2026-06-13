"""Request and response data models.

Request DTOs (``TemplateSend``, ``RawSend``, the ``*Content`` classes,
``Attachment``) are plain dataclasses you construct; response models expose a
``from_dict`` classmethod that parses the wire JSON defensively (unknown fields
are ignored, missing ones get sensible defaults). ``Message`` keeps the full
decoded body in ``.raw`` so new API fields are reachable without an SDK bump.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from .errors import SenderKitError


class Channel(str, Enum):
    """Delivery channels. Subclasses ``str`` so it serializes to its value."""

    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    WEB_PUSH = "web-push"


ChannelLike = Union[Channel, str]
ScheduledAt = Union[str, datetime]
Vars = Dict[str, Any]
Metadata = Dict[str, Union[str, int, float, bool]]


# --------------------------------------------------------------------------- #
# Raw-send content
# --------------------------------------------------------------------------- #
@dataclass
class Attachment:
    """An email attachment. ``content`` is base64-encoded bytes."""

    filename: str
    content_type: str
    content: str
    inline: Optional[bool] = None
    content_id: Optional[str] = None


@dataclass
class EmailContent:
    """Inline email content for a raw send."""

    subject: str
    html: str
    preheader: Optional[str] = None
    text: Optional[str] = None
    cc: Optional[List[str]] = None
    bcc: Optional[List[str]] = None
    reply_to: Optional[str] = None
    attachments: Optional[List[Attachment]] = None


@dataclass
class SmsContent:
    """Inline SMS content for a raw send."""

    body: str


@dataclass
class PushContent:
    """Inline mobile-push content for a raw send."""

    title: str
    body: str
    data: Optional[Dict[str, str]] = None
    badge: Optional[int] = None
    sound: Optional[str] = None


@dataclass
class WebPushContent:
    """Inline web-push content for a raw send."""

    title: str
    body: str
    icon: Optional[str] = None
    click_url: Optional[str] = None
    data: Optional[Dict[str, str]] = None
    badge: Optional[int] = None


Content = Union[EmailContent, SmsContent, PushContent, WebPushContent]


# --------------------------------------------------------------------------- #
# Request DTOs
# --------------------------------------------------------------------------- #
@dataclass
class TemplateSend:
    """A send backed by a stored template. Built for you by ``client.send(...)``;
    construct it directly to queue items for ``client.send_batch(...)``."""

    template: str
    to: str
    vars: Optional[Vars] = None
    version: Optional[int] = None
    channel: Optional[ChannelLike] = None
    metadata: Optional[Metadata] = None
    scheduled_at: Optional[ScheduledAt] = None
    cc: Optional[List[str]] = None
    bcc: Optional[List[str]] = None
    reply_to: Optional[str] = None
    attachments: Optional[List[Attachment]] = None
    idempotency_key: Optional[str] = None


@dataclass
class RawSend:
    """A send with inline content, bypassing templates. ``channel`` is inferred
    from ``content`` when omitted. ``from_`` maps to the wire field ``from``."""

    to: str
    content: Content
    channel: Optional[ChannelLike] = None
    from_: Optional[str] = None
    interpolate: Optional[bool] = None
    vars: Optional[Vars] = None
    metadata: Optional[Metadata] = None
    scheduled_at: Optional[ScheduledAt] = None
    idempotency_key: Optional[str] = None


# --------------------------------------------------------------------------- #
# Response models
# --------------------------------------------------------------------------- #
@dataclass
class SendResult:
    """Returned by ``send`` / ``send_raw`` — the queued message's id and status."""

    id: str
    status: str
    livemode: bool

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> SendResult:
        return cls(
            id=str(d.get("id", "")),
            status=str(d.get("status", "")),
            livemode=bool(d.get("livemode", False)),
        )


@dataclass
class BatchResult:
    """One entry in a ``send_batch`` result, positionally aligned with the input."""

    ok: bool
    index: int
    result: Optional[SendResult] = None
    error: Optional[SenderKitError] = None


@dataclass
class Message:
    """A message record. Common fields are typed; ``.raw`` holds the full body."""

    id: str
    public_id: str
    status: str
    channel: str
    template_slug: Optional[str]
    recipient: str
    created_at: str
    raw: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> Message:
        return cls(
            id=str(d.get("id", "")),
            public_id=str(d.get("publicId", "")),
            status=str(d.get("status", "")),
            channel=str(d.get("channel", "")),
            template_slug=d.get("templateSlug"),
            recipient=str(d.get("recipient", "")),
            created_at=str(d.get("createdAt", "")),
            raw=d,
        )


@dataclass
class MessageList:
    """A page of messages. ``next_cursor`` is ``None`` on the last page."""

    data: List[Message]
    next_cursor: Optional[str]

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> MessageList:
        items = d.get("data") or []
        return cls(
            data=[Message.from_dict(m) for m in items],
            next_cursor=d.get("nextCursor"),
        )


@dataclass
class CancelResult:
    """Returned by ``messages.cancel`` — the message id and its terminal status."""

    id: str
    status: str

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> CancelResult:
        return cls(id=str(d.get("id", "")), status=str(d.get("status", "")))


@dataclass
class TemplateVariable:
    name: str
    type: str
    description: Optional[str] = None
    required: bool = False

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> TemplateVariable:
        return cls(
            name=str(d.get("name", "")),
            type=str(d.get("type", "")),
            description=d.get("description"),
            required=bool(d.get("required", False)),
        )


@dataclass
class TemplateVersion:
    version_number: int
    variables: List[TemplateVariable]
    published_at: Optional[str]

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> TemplateVersion:
        raw_vars = d.get("variables") or []
        variables = [TemplateVariable.from_dict(v) for v in raw_vars if isinstance(v, dict)]
        return cls(
            version_number=int(d.get("versionNumber", 0)),
            variables=variables,
            published_at=d.get("publishedAt"),
        )


@dataclass
class TemplateSummary:
    slug: str
    channel: str
    description: Optional[str]
    status: str
    updated_at: str

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> TemplateSummary:
        return cls(
            slug=str(d.get("slug", "")),
            channel=str(d.get("channel", "")),
            description=d.get("description"),
            status=str(d.get("status", "")),
            updated_at=str(d.get("updatedAt", "")),
        )


@dataclass
class TemplateDetail:
    slug: str
    channel: str
    description: Optional[str]
    status: str
    updated_at: str
    current_version: Optional[TemplateVersion]

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> TemplateDetail:
        cv = d.get("currentVersion")
        return cls(
            slug=str(d.get("slug", "")),
            channel=str(d.get("channel", "")),
            description=d.get("description"),
            status=str(d.get("status", "")),
            updated_at=str(d.get("updatedAt", "")),
            current_version=TemplateVersion.from_dict(cv) if isinstance(cv, dict) else None,
        )


@dataclass
class RenderResult:
    channel: str
    output: Dict[str, Any]
    missing: List[str]

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> RenderResult:
        return cls(
            channel=str(d.get("channel", "")),
            output=d.get("output") or {},
            missing=list(d.get("missing") or []),
        )


@dataclass
class Workspace:
    id: str
    slug: str
    name: str

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> Workspace:
        return cls(
            id=str(d.get("id", "")),
            slug=str(d.get("slug", "")),
            name=str(d.get("name", "")),
        )


@dataclass
class Context:
    workspace: Workspace
    mode: str

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> Context:
        ws = d.get("workspace")
        return cls(
            workspace=Workspace.from_dict(ws if isinstance(ws, dict) else {}),
            mode=str(d.get("mode", "")),
        )
