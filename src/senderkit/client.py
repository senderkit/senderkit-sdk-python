"""The public client: ``SenderKit`` (sync) and ``AsyncSenderKit`` (async).

Both expose the same surface as the TypeScript and PHP SDKs — ``send``,
``send_raw``, ``send_batch``, ``context``, plus the ``messages`` and
``templates`` resource namespaces — and both work as (async) context managers.
"""

from __future__ import annotations

import asyncio
import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Optional, Sequence, Union

import httpx

from . import errors
from ._http import AsyncTransport, Transport
from ._serialize import build_send
from .models import (
    BatchResult,
    ChannelLike,
    Content,
    Context,
    RawSend,
    ScheduledAt,
    SendResult,
    TemplateSend,
)
from .resources import AsyncMessages, AsyncTemplates, Messages, Templates

DEFAULT_BASE_URL = "https://api.senderkit.com"
DEFAULT_TIMEOUT = 30.0
DEFAULT_MAX_RETRIES = 2

SendItem = Union[TemplateSend, RawSend]


def _mode_for_key(api_key: str) -> str:
    return "test" if api_key.startswith("sk_test_") else "live"


def _batch_key(base: Optional[str], item: SendItem, index: int) -> str:
    """Per-item idempotency key: ``{base}-{index}`` if a base was given, else the
    item's own key, else a fresh UUID."""
    if base:
        return f"{base}-{index}"
    return item.idempotency_key or str(uuid.uuid4())


class SenderKit:
    """Synchronous SenderKit client.

    ``timeout`` is in seconds (httpx convention; the TS/PHP SDKs use milliseconds).
    Pass your own ``httpx.Client`` to control proxies, TLS, or connection pooling.
    """

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        http_client: Optional[httpx.Client] = None,
    ) -> None:
        if not api_key:
            raise ValueError("api_key is required")
        self.mode = _mode_for_key(api_key)
        self._transport = Transport(api_key, base_url, timeout, max_retries, http_client)
        self.messages = Messages(self._transport)
        self.templates = Templates(self._transport)

    def send(
        self,
        template: str,
        to: str,
        *,
        vars: Optional[Dict[str, Any]] = None,
        version: Optional[int] = None,
        channel: Optional[ChannelLike] = None,
        metadata: Optional[Dict[str, Any]] = None,
        scheduled_at: Optional[ScheduledAt] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        reply_to: Optional[str] = None,
        attachments: Optional[list] = None,
        idempotency_key: Optional[str] = None,
    ) -> SendResult:
        """Send a stored template to one recipient."""
        return self._send(
            TemplateSend(
                template=template,
                to=to,
                vars=vars,
                version=version,
                channel=channel,
                metadata=metadata,
                scheduled_at=scheduled_at,
                cc=cc,
                bcc=bcc,
                reply_to=reply_to,
                attachments=attachments,
                idempotency_key=idempotency_key,
            )
        )

    def send_raw(
        self,
        to: str,
        content: Content,
        *,
        channel: Optional[ChannelLike] = None,
        from_: Optional[str] = None,
        interpolate: Optional[bool] = None,
        vars: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        scheduled_at: Optional[ScheduledAt] = None,
        idempotency_key: Optional[str] = None,
    ) -> SendResult:
        """Send inline content (no template). ``channel`` is inferred from ``content``."""
        return self._send(
            RawSend(
                to=to,
                content=content,
                channel=channel,
                from_=from_,
                interpolate=interpolate,
                vars=vars,
                metadata=metadata,
                scheduled_at=scheduled_at,
                idempotency_key=idempotency_key,
            )
        )

    def _send(self, request: SendItem, idempotency_key: Optional[str] = None) -> SendResult:
        body, own_key = build_send(request)
        key = idempotency_key or own_key or str(uuid.uuid4())
        data = self._transport.request_json("POST", "/v1/send", body=body, idempotency_key=key)
        return SendResult.from_dict(data)

    def send_batch(
        self,
        requests: Sequence[SendItem],
        *,
        concurrency: int = 5,
        idempotency_key: Optional[str] = None,
    ) -> List[BatchResult]:
        """Send many messages concurrently. Each result is positionally aligned
        with ``requests``; a per-item failure becomes a ``BatchResult(ok=False)``
        rather than aborting the batch."""
        results: List[Optional[BatchResult]] = [None] * len(requests)

        def run(index: int, request: SendItem) -> BatchResult:
            try:
                key = _batch_key(idempotency_key, request, index)
                result = self._send(request, idempotency_key=key)
                return BatchResult(ok=True, index=index, result=result)
            except errors.SenderKitError as exc:
                return BatchResult(ok=False, index=index, error=exc)

        if not requests:
            return []

        with ThreadPoolExecutor(max_workers=max(1, concurrency)) as pool:
            for outcome in pool.map(lambda pair: run(*pair), list(enumerate(requests))):
                results[outcome.index] = outcome

        return [r for r in results if r is not None]

    def context(self) -> Context:
        """Return the workspace and mode this API key operates in."""
        return Context.from_dict(self._transport.request_json("GET", "/v1/context"))

    def close(self) -> None:
        self._transport.close()

    def __enter__(self) -> SenderKit:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()


class AsyncSenderKit:
    """Asynchronous SenderKit client. Mirrors :class:`SenderKit` with ``await``."""

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        http_client: Optional[httpx.AsyncClient] = None,
    ) -> None:
        if not api_key:
            raise ValueError("api_key is required")
        self.mode = _mode_for_key(api_key)
        self._transport = AsyncTransport(api_key, base_url, timeout, max_retries, http_client)
        self.messages = AsyncMessages(self._transport)
        self.templates = AsyncTemplates(self._transport)

    async def send(
        self,
        template: str,
        to: str,
        *,
        vars: Optional[Dict[str, Any]] = None,
        version: Optional[int] = None,
        channel: Optional[ChannelLike] = None,
        metadata: Optional[Dict[str, Any]] = None,
        scheduled_at: Optional[ScheduledAt] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        reply_to: Optional[str] = None,
        attachments: Optional[list] = None,
        idempotency_key: Optional[str] = None,
    ) -> SendResult:
        return await self._send(
            TemplateSend(
                template=template,
                to=to,
                vars=vars,
                version=version,
                channel=channel,
                metadata=metadata,
                scheduled_at=scheduled_at,
                cc=cc,
                bcc=bcc,
                reply_to=reply_to,
                attachments=attachments,
                idempotency_key=idempotency_key,
            )
        )

    async def send_raw(
        self,
        to: str,
        content: Content,
        *,
        channel: Optional[ChannelLike] = None,
        from_: Optional[str] = None,
        interpolate: Optional[bool] = None,
        vars: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        scheduled_at: Optional[ScheduledAt] = None,
        idempotency_key: Optional[str] = None,
    ) -> SendResult:
        return await self._send(
            RawSend(
                to=to,
                content=content,
                channel=channel,
                from_=from_,
                interpolate=interpolate,
                vars=vars,
                metadata=metadata,
                scheduled_at=scheduled_at,
                idempotency_key=idempotency_key,
            )
        )

    async def _send(self, request: SendItem, idempotency_key: Optional[str] = None) -> SendResult:
        body, own_key = build_send(request)
        key = idempotency_key or own_key or str(uuid.uuid4())
        data = await self._transport.request_json(
            "POST", "/v1/send", body=body, idempotency_key=key
        )
        return SendResult.from_dict(data)

    async def send_batch(
        self,
        requests: Sequence[SendItem],
        *,
        concurrency: int = 5,
        idempotency_key: Optional[str] = None,
    ) -> List[BatchResult]:
        if not requests:
            return []
        semaphore = asyncio.Semaphore(max(1, concurrency))

        async def run(index: int, request: SendItem) -> BatchResult:
            async with semaphore:
                try:
                    key = _batch_key(idempotency_key, request, index)
                    result = await self._send(request, idempotency_key=key)
                    return BatchResult(ok=True, index=index, result=result)
                except errors.SenderKitError as exc:
                    return BatchResult(ok=False, index=index, error=exc)

        outcomes = await asyncio.gather(*(run(i, r) for i, r in enumerate(requests)))
        return sorted(outcomes, key=lambda r: r.index)

    async def context(self) -> Context:
        return Context.from_dict(await self._transport.request_json("GET", "/v1/context"))

    async def aclose(self) -> None:
        await self._transport.aclose()

    async def __aenter__(self) -> AsyncSenderKit:
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.aclose()
