"""Turn request DTOs into the JSON shapes the API expects.

Centralizes the snake_case → camelCase mapping, ``None`` pruning, datetime →
ISO-8601 conversion, and enum unwrapping so the client and resources never
hand-build wire dicts. Kept explicit (rather than reflection-based) so the
mapping is auditable against ``openapi.yaml``.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional, Tuple

from .models import (
    Attachment,
    Channel,
    ChannelLike,
    Content,
    EmailContent,
    PushContent,
    RawSend,
    SmsContent,
    TemplateSend,
    WebPushContent,
)


def _iso(value: Any) -> Any:
    """ISO-8601 string for a datetime; pass strings (and None) through."""
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def _channel_value(channel: Optional[ChannelLike]) -> Optional[str]:
    if channel is None:
        return None
    return channel.value if isinstance(channel, Channel) else str(channel)


def _prune(d: Dict[str, Any]) -> Dict[str, Any]:
    """Drop keys whose value is ``None`` (omit-if-absent semantics)."""
    return {k: v for k, v in d.items() if v is not None}


def _attachment_to_wire(a: Attachment) -> Dict[str, Any]:
    return _prune(
        {
            "filename": a.filename,
            "contentType": a.content_type,
            "content": a.content,
            "inline": a.inline,
            "contentId": a.content_id,
        }
    )


def channel_for_content(content: Content) -> str:
    """Infer the channel string from a content instance."""
    if isinstance(content, EmailContent):
        return "email"
    if isinstance(content, SmsContent):
        return "sms"
    if isinstance(content, PushContent):
        return "push"
    if isinstance(content, WebPushContent):
        return "web-push"
    raise TypeError(f"Unsupported content type: {type(content)!r}")


def content_to_wire(content: Content) -> Dict[str, Any]:
    if isinstance(content, EmailContent):
        return _prune(
            {
                "subject": content.subject,
                "preheader": content.preheader,
                "html": content.html,
                "text": content.text,
                "cc": content.cc,
                "bcc": content.bcc,
                "replyTo": content.reply_to,
                "attachments": (
                    [_attachment_to_wire(a) for a in content.attachments]
                    if content.attachments
                    else None
                ),
            }
        )
    if isinstance(content, SmsContent):
        return {"body": content.body}
    if isinstance(content, PushContent):
        return _prune(
            {
                "title": content.title,
                "body": content.body,
                "data": content.data,
                "badge": content.badge,
                "sound": content.sound,
            }
        )
    if isinstance(content, WebPushContent):
        return _prune(
            {
                "title": content.title,
                "body": content.body,
                "icon": content.icon,
                "clickUrl": content.click_url,
                "data": content.data,
                "badge": content.badge,
            }
        )
    raise TypeError(f"Unsupported content type: {type(content)!r}")


def template_send_to_body(req: TemplateSend) -> Dict[str, Any]:
    return _prune(
        {
            "template": req.template,
            "to": req.to,
            "vars": req.vars,
            "version": req.version,
            "channel": _channel_value(req.channel),
            "metadata": req.metadata,
            "scheduledAt": _iso(req.scheduled_at),
            "cc": req.cc,
            "bcc": req.bcc,
            "replyTo": req.reply_to,
            "attachments": (
                [_attachment_to_wire(a) for a in req.attachments] if req.attachments else None
            ),
        }
    )


def raw_send_to_body(req: RawSend) -> Dict[str, Any]:
    channel = _channel_value(req.channel) or channel_for_content(req.content)
    return _prune(
        {
            "channel": channel,
            "to": req.to,
            "from": req.from_,
            "interpolate": req.interpolate,
            "content": content_to_wire(req.content),
            "vars": req.vars,
            "metadata": req.metadata,
            "scheduledAt": _iso(req.scheduled_at),
        }
    )


def build_send(req: Any) -> Tuple[Dict[str, Any], Optional[str]]:
    """Serialize a send request, returning ``(body, idempotency_key)``."""
    if isinstance(req, TemplateSend):
        return template_send_to_body(req), req.idempotency_key
    if isinstance(req, RawSend):
        return raw_send_to_body(req), req.idempotency_key
    raise TypeError(f"Expected TemplateSend or RawSend, got {type(req)!r}")


def list_messages_query(
    *,
    limit: Optional[int],
    cursor: Optional[str],
    status: Optional[str],
    channel: Optional[ChannelLike],
    template: Optional[str],
    metadata: Optional[Dict[str, Any]],
    tail: Optional[str],
) -> Dict[str, Any]:
    """Build the query dict for ``GET /v1/messages``, including ``metadata[key]``."""
    query: Dict[str, Any] = _prune(
        {
            "limit": limit,
            "cursor": cursor,
            "status": status.value if isinstance(status, Channel) else status,
            "channel": _channel_value(channel),
            "template": template,
            "tail": tail,
        }
    )
    if metadata:
        for key, value in metadata.items():
            query[f"metadata[{key}]"] = value
    return query
