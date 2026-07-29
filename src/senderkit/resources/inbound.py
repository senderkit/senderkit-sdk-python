"""The ``inbound`` resource: provision receiving addresses and read received mail.

Requires an API key with the ``inbound`` scope. Exposed on the client as
``client.inbound.addresses`` and ``client.inbound.messages``.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from urllib.parse import unquote

from .._http import AsyncTransport, Transport
from ..models import (
    InboundAddress,
    InboundBytes,
    InboundDomain,
    InboundMessage,
    InboundMessageSummary,
)

BeforeLike = Union[str, datetime]


def _iso(value: Optional[BeforeLike]) -> Optional[str]:
    if value is None:
        return None
    return value.isoformat() if isinstance(value, datetime) else value


def _create_body(
    local_part: Optional[str],
    description: Optional[str],
    forward_to: Optional[str],
    webhook_endpoint_id: Optional[str],
    domain_id: Optional[str],
    livemode: Optional[bool],
) -> Dict[str, Any]:
    body: Dict[str, Any] = {}
    if local_part is not None:
        body["localPart"] = local_part
    if description is not None:
        body["description"] = description
    if forward_to is not None:
        body["forwardTo"] = forward_to
    if webhook_endpoint_id is not None:
        body["webhookEndpointId"] = webhook_endpoint_id
    if domain_id is not None:
        body["domainId"] = domain_id
    if livemode is not None:
        body["livemode"] = livemode
    return body


def _domain_create_body(domain: str, acknowledge_existing_mx: Optional[bool]) -> Dict[str, Any]:
    if not domain:
        raise ValueError("inbound.domains.create: domain is required")
    body: Dict[str, Any] = {"domain": domain}
    if acknowledge_existing_mx is not None:
        body["acknowledgeExistingMx"] = acknowledge_existing_mx
    return body


def _list_query(
    limit: Optional[int], before: Optional[BeforeLike], address: Optional[str]
) -> Dict[str, Any]:
    return {"limit": limit, "before": _iso(before), "address": address}


def _filename(content_disposition: Optional[str]) -> Optional[str]:
    """Pull a filename from a Content-Disposition header (RFC 5987 aware)."""
    if not content_disposition:
        return None
    extended = re.search(r"filename\*\s*=\s*(?:[^']*'[^']*')?([^;]+)", content_disposition, re.I)
    if extended:
        return unquote(extended.group(1).strip())
    plain = re.search(r'filename\s*=\s*"?([^";]+)"?', content_disposition, re.I)
    return plain.group(1).strip() if plain else None


def _to_bytes(response: Any) -> InboundBytes:
    return InboundBytes(
        content=response.content,
        content_type=response.headers.get("content-type", "application/octet-stream"),
        filename=_filename(response.headers.get("content-disposition")),
    )


class InboundAddresses:
    """Synchronous inbound-address operations."""

    def __init__(self, transport: Transport) -> None:
        self._t = transport

    def list(self) -> List[InboundAddress]:
        """Return every inbound address on the workspace's shared domain, oldest first."""
        data = self._t.request_json("GET", "/v1/inbound/addresses")
        rows = data.get("addresses") or []
        return [InboundAddress.from_dict(a) for a in rows]

    def create(
        self,
        *,
        local_part: Optional[str] = None,
        description: Optional[str] = None,
        forward_to: Optional[str] = None,
        webhook_endpoint_id: Optional[str] = None,
        domain_id: Optional[str] = None,
        livemode: Optional[bool] = None,
    ) -> InboundAddress:
        """Provision a new address. Omit ``local_part`` for an auto-generated one;
        pass ``"*"`` for a catch-all. ``domain_id`` mints on a verified custom
        domain; ``livemode`` sets the mode (defaults to live)."""
        body = _create_body(
            local_part, description, forward_to, webhook_endpoint_id, domain_id, livemode
        )
        return InboundAddress.from_dict(
            self._t.request_json("POST", "/v1/inbound/addresses", body=body)
        )

    def delete(self, id: str) -> bool:
        """Soft-delete an address; later mail to it is dropped. Returns ``True``."""
        data = self._t.request_json("DELETE", f"/v1/inbound/addresses/{id}")
        return bool(data.get("deleted", False))


class InboundMessages:
    """Synchronous received-message operations."""

    def __init__(self, transport: Transport) -> None:
        self._t = transport

    def list(
        self,
        *,
        limit: Optional[int] = None,
        before: Optional[BeforeLike] = None,
        address: Optional[str] = None,
    ) -> List[InboundMessageSummary]:
        """Return received-message summaries, newest first."""
        data = self._t.request_json(
            "GET", "/v1/inbound/messages", query=_list_query(limit, before, address)
        )
        rows = data.get("messages") or []
        return [InboundMessageSummary.from_dict(m) for m in rows]

    def get(self, id: str) -> InboundMessage:
        """Retrieve a received message, including body, headers, and verdicts."""
        return InboundMessage.from_dict(self._t.request_json("GET", f"/v1/inbound/messages/{id}"))

    def raw(self, id: str) -> InboundBytes:
        """Fetch the raw RFC 822 source. 410s past the 30-day retention window."""
        resp = self._t.request("GET", f"/v1/inbound/messages/{id}/raw", accept="message/rfc822")
        return _to_bytes(resp)

    def attachment(self, id: str, index: int) -> InboundBytes:
        """Fetch one attachment's bytes by its zero-based ``index``."""
        resp = self._t.request(
            "GET",
            f"/v1/inbound/messages/{id}/attachments/{index}",
            accept="application/octet-stream",
        )
        return _to_bytes(resp)


class InboundDomains:
    """Synchronous custom-inbound-domain operations."""

    def __init__(self, transport: Transport) -> None:
        self._t = transport

    def list(self) -> List[InboundDomain]:
        """Return the workspace's inbound domains (shared + custom)."""
        data = self._t.request_json("GET", "/v1/inbound/domains")
        rows = data.get("domains") or []
        return [InboundDomain.from_dict(d) for d in rows]

    def create(
        self, domain: str, *, acknowledge_existing_mx: Optional[bool] = None
    ) -> InboundDomain:
        """Claim a custom domain for receiving. The result carries the DNS
        records to publish. If the domain already has live MX records elsewhere,
        this raises a 409 ``SenderKitAPIError`` (``existing_mx``) — confirm with
        the user, then retry with ``acknowledge_existing_mx=True``."""
        body = _domain_create_body(domain, acknowledge_existing_mx)
        return InboundDomain.from_dict(
            self._t.request_json("POST", "/v1/inbound/domains", body=body)
        )

    def delete(self, id: str) -> bool:
        """Delete a custom inbound domain. The shared domain cannot be deleted."""
        data = self._t.request_json("DELETE", f"/v1/inbound/domains/{id}")
        return bool(data.get("deleted", False))


class Inbound:
    """Synchronous ``inbound`` namespace: ``addresses``, ``messages``, ``domains``."""

    def __init__(self, transport: Transport) -> None:
        self.addresses = InboundAddresses(transport)
        self.messages = InboundMessages(transport)
        self.domains = InboundDomains(transport)


class AsyncInboundAddresses:
    """Asynchronous inbound-address operations."""

    def __init__(self, transport: AsyncTransport) -> None:
        self._t = transport

    async def list(self) -> List[InboundAddress]:
        data = await self._t.request_json("GET", "/v1/inbound/addresses")
        rows = data.get("addresses") or []
        return [InboundAddress.from_dict(a) for a in rows]

    async def create(
        self,
        *,
        local_part: Optional[str] = None,
        description: Optional[str] = None,
        forward_to: Optional[str] = None,
        webhook_endpoint_id: Optional[str] = None,
        domain_id: Optional[str] = None,
        livemode: Optional[bool] = None,
    ) -> InboundAddress:
        body = _create_body(
            local_part, description, forward_to, webhook_endpoint_id, domain_id, livemode
        )
        return InboundAddress.from_dict(
            await self._t.request_json("POST", "/v1/inbound/addresses", body=body)
        )

    async def delete(self, id: str) -> bool:
        data = await self._t.request_json("DELETE", f"/v1/inbound/addresses/{id}")
        return bool(data.get("deleted", False))


class AsyncInboundMessages:
    """Asynchronous received-message operations."""

    def __init__(self, transport: AsyncTransport) -> None:
        self._t = transport

    async def list(
        self,
        *,
        limit: Optional[int] = None,
        before: Optional[BeforeLike] = None,
        address: Optional[str] = None,
    ) -> List[InboundMessageSummary]:
        data = await self._t.request_json(
            "GET", "/v1/inbound/messages", query=_list_query(limit, before, address)
        )
        rows = data.get("messages") or []
        return [InboundMessageSummary.from_dict(m) for m in rows]

    async def get(self, id: str) -> InboundMessage:
        return InboundMessage.from_dict(
            await self._t.request_json("GET", f"/v1/inbound/messages/{id}")
        )

    async def raw(self, id: str) -> InboundBytes:
        resp = await self._t.request(
            "GET", f"/v1/inbound/messages/{id}/raw", accept="message/rfc822"
        )
        return _to_bytes(resp)

    async def attachment(self, id: str, index: int) -> InboundBytes:
        resp = await self._t.request(
            "GET",
            f"/v1/inbound/messages/{id}/attachments/{index}",
            accept="application/octet-stream",
        )
        return _to_bytes(resp)


class AsyncInboundDomains:
    """Asynchronous custom-inbound-domain operations."""

    def __init__(self, transport: AsyncTransport) -> None:
        self._t = transport

    async def list(self) -> List[InboundDomain]:
        data = await self._t.request_json("GET", "/v1/inbound/domains")
        rows = data.get("domains") or []
        return [InboundDomain.from_dict(d) for d in rows]

    async def create(
        self, domain: str, *, acknowledge_existing_mx: Optional[bool] = None
    ) -> InboundDomain:
        body = _domain_create_body(domain, acknowledge_existing_mx)
        return InboundDomain.from_dict(
            await self._t.request_json("POST", "/v1/inbound/domains", body=body)
        )

    async def delete(self, id: str) -> bool:
        data = await self._t.request_json("DELETE", f"/v1/inbound/domains/{id}")
        return bool(data.get("deleted", False))


class AsyncInbound:
    """Asynchronous ``inbound`` namespace: ``addresses``, ``messages``, ``domains``."""

    def __init__(self, transport: AsyncTransport) -> None:
        self.addresses = AsyncInboundAddresses(transport)
        self.messages = AsyncInboundMessages(transport)
        self.domains = AsyncInboundDomains(transport)
