"""A Django ``EMAIL_BACKEND`` that routes mail through SenderKit's raw-send API.

Because Django renders messages locally, sends through this backend bypass
SenderKit templates (you lose versioning, preview, and per-template analytics).
Use it to migrate an existing ``django.core.mail`` app without code changes; for
new code, prefer ``get_client().send(...)`` with a template.

Messages with multiple ``to`` recipients are fanned out as one API call each,
since the API addresses a single recipient per send (mirrors the PHP Laravel
``SenderKitTransport``).
"""

from __future__ import annotations

import base64
from email.mime.base import MIMEBase
from typing import Any, List, Optional

from django.core.mail.backends.base import BaseEmailBackend

from ...errors import SenderKitError
from ...models import Attachment, EmailContent
from .client import get_client


def _to_text(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, bytes):
        return value.decode("utf-8", "replace")
    return str(value)


def _html_body(message: Any) -> str:
    """The API requires HTML. Prefer an explicit text/html alternative, then an
    html ``content_subtype`` body, falling back to an escaped plain-text body."""
    for content, mimetype in getattr(message, "alternatives", None) or []:
        if mimetype == "text/html":
            return _to_text(content) or ""
    if getattr(message, "content_subtype", "plain") == "html":
        return _to_text(message.body) or ""
    from django.utils.html import escape

    return escape(_to_text(message.body) or "").replace("\n", "<br>")


def _text_body(message: Any) -> Optional[str]:
    if getattr(message, "content_subtype", "plain") == "html":
        return None
    return _to_text(message.body)


def _addresses(values: Any) -> Optional[List[str]]:
    items = [v for v in (values or []) if v]
    return items or None


def _attachments(message: Any) -> Optional[List[Attachment]]:
    out: List[Attachment] = []
    for attachment in getattr(message, "attachments", None) or []:
        if isinstance(attachment, MIMEBase):
            filename = attachment.get_filename() or "attachment"
            content_type = attachment.get_content_type()
            decoded = attachment.get_payload(decode=True)
            payload = decoded if isinstance(decoded, (bytes, bytearray)) else b""
            content = base64.b64encode(payload).decode()
        else:
            filename, raw, content_type = attachment
            data = raw.encode() if isinstance(raw, str) else raw
            content = base64.b64encode(data).decode()
        out.append(
            Attachment(
                filename=filename or "attachment",
                content_type=content_type or "application/octet-stream",
                content=content,
            )
        )
    return out or None


class EmailBackend(BaseEmailBackend):
    """Sends Django email messages via SenderKit raw email sends."""

    def send_messages(self, email_messages: Any) -> int:
        if not email_messages:
            return 0
        client = get_client()
        sent = 0
        for message in email_messages:
            content = EmailContent(
                subject=str(message.subject or ""),
                html=_html_body(message),
                text=_text_body(message),
                cc=_addresses(getattr(message, "cc", None)),
                bcc=_addresses(getattr(message, "bcc", None)),
                reply_to=(getattr(message, "reply_to", None) or [None])[0],
                attachments=_attachments(message),
            )
            from_email = message.from_email or None
            recipients = getattr(message, "to", None) or []
            try:
                for recipient in recipients:
                    client.send_raw(recipient, content, from_=from_email)
                    sent += 1
            except SenderKitError:
                if not self.fail_silently:
                    raise
        return sent
