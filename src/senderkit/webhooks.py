"""Verify inbound webhook signatures (HMAC-SHA256), ported from the PHP SDK.

Header format: ``X-SenderKit-Signature: t=<unix>,v1=<hex>``. The signed string
is ``f"{t}.{raw_body}"`` — verify against the *raw* request body, before any
JSON decoding. Use this directly, or via the framework integrations which read
the header and body for you.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple, Union

from .errors import SignatureVerificationError

DEFAULT_TOLERANCE_SECONDS = 300


@dataclass
class WebhookEvent:
    """A verified webhook. ``type``/``delivery_id`` are passed through from the
    ``X-SenderKit-Event`` / ``X-SenderKit-Delivery`` headers; ``payload`` is the
    decoded JSON body (``{}`` if the body was not a JSON object)."""

    type: Optional[str]
    delivery_id: Optional[str]
    payload: Dict[str, Any]
    timestamp: int


def _parse_header(header: str) -> Tuple[int, str]:
    timestamp: Optional[int] = None
    signature: Optional[str] = None
    for part in header.split(","):
        pair = part.strip().split("=", 1)
        if len(pair) != 2:
            continue
        key, value = pair
        if key == "t" and value.isdigit():
            timestamp = int(value)
        elif key == "v1":
            signature = value
    if timestamp is None or not signature:
        raise SignatureVerificationError("Malformed signature header.")
    return timestamp, signature


class WebhookVerifier:
    """Verifies webhook signatures. Construct with a default ``secret`` (``whsec_…``),
    or pass ``secret=`` per call."""

    def __init__(self, secret: Optional[str] = None) -> None:
        self._secret = secret

    def verify(
        self,
        payload: Union[str, bytes],
        signature_header: str,
        *,
        secret: Optional[str] = None,
        tolerance: int = DEFAULT_TOLERANCE_SECONDS,
        now: Optional[int] = None,
        event_type: Optional[str] = None,
        delivery_id: Optional[str] = None,
    ) -> WebhookEvent:
        """Verify ``payload`` against ``signature_header``; return the event or raise.

        Raises :class:`SignatureVerificationError` on an empty secret, a malformed
        header, a timestamp outside ``tolerance`` seconds, or a signature mismatch.
        """
        secret = secret or self._secret
        if not secret:
            raise SignatureVerificationError("Webhook signing secret must not be empty.")

        raw = payload.decode() if isinstance(payload, (bytes, bytearray)) else payload
        timestamp, signature = _parse_header(signature_header)

        current = int(time.time()) if now is None else now
        if abs(current - timestamp) > tolerance:
            raise SignatureVerificationError("Webhook timestamp outside tolerance window.")

        expected = hmac.new(
            secret.encode(), f"{timestamp}.{raw}".encode(), hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(expected, signature):
            raise SignatureVerificationError("Webhook signature mismatch.")

        try:
            decoded = json.loads(raw)
            payload_dict = decoded if isinstance(decoded, dict) else {}
        except (ValueError, TypeError):
            payload_dict = {}

        return WebhookEvent(
            type=event_type,
            delivery_id=delivery_id,
            payload=payload_dict,
            timestamp=timestamp,
        )
