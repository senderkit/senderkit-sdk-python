"""The ``messages`` resource: list (with auto-pagination), get, and cancel."""

from __future__ import annotations

from typing import Any, AsyncIterator, Dict, Iterator, Optional

from .._http import AsyncTransport, Transport
from .._serialize import list_messages_query
from ..models import CancelResult, ChannelLike, Message, MessageList


class Messages:
    """Synchronous message operations."""

    def __init__(self, transport: Transport) -> None:
        self._t = transport

    def list(
        self,
        *,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
        status: Optional[str] = None,
        channel: Optional[ChannelLike] = None,
        template: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tail: Optional[str] = None,
    ) -> MessageList:
        """Return one page of messages, newest first, with a cursor for the next."""
        query = list_messages_query(
            limit=limit,
            cursor=cursor,
            status=status,
            channel=channel,
            template=template,
            metadata=metadata,
            tail=tail,
        )
        return MessageList.from_dict(
            self._t.request_json("GET", "/v1/messages", query=query)
        )

    def iter(
        self,
        *,
        limit: Optional[int] = None,
        status: Optional[str] = None,
        channel: Optional[ChannelLike] = None,
        template: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Iterator[Message]:
        """Yield every matching message, following ``next_cursor`` across pages."""
        cursor: Optional[str] = None
        while True:
            page = self.list(
                limit=limit,
                cursor=cursor,
                status=status,
                channel=channel,
                template=template,
                metadata=metadata,
            )
            yield from page.data
            if not page.next_cursor:
                return
            cursor = page.next_cursor

    def get(self, id: str) -> Message:
        """Retrieve a single message by its public id (``msg_...``)."""
        return Message.from_dict(self._t.request_json("GET", f"/v1/messages/{id}"))

    def cancel(self, id: str) -> CancelResult:
        """Cancel a still-pending (scheduled or queued) message."""
        return CancelResult.from_dict(
            self._t.request_json("DELETE", f"/v1/messages/{id}")
        )


class AsyncMessages:
    """Asynchronous message operations."""

    def __init__(self, transport: AsyncTransport) -> None:
        self._t = transport

    async def list(
        self,
        *,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
        status: Optional[str] = None,
        channel: Optional[ChannelLike] = None,
        template: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tail: Optional[str] = None,
    ) -> MessageList:
        query = list_messages_query(
            limit=limit,
            cursor=cursor,
            status=status,
            channel=channel,
            template=template,
            metadata=metadata,
            tail=tail,
        )
        return MessageList.from_dict(
            await self._t.request_json("GET", "/v1/messages", query=query)
        )

    async def aiter(
        self,
        *,
        limit: Optional[int] = None,
        status: Optional[str] = None,
        channel: Optional[ChannelLike] = None,
        template: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AsyncIterator[Message]:
        cursor: Optional[str] = None
        while True:
            page = await self.list(
                limit=limit,
                cursor=cursor,
                status=status,
                channel=channel,
                template=template,
                metadata=metadata,
            )
            for message in page.data:
                yield message
            if not page.next_cursor:
                return
            cursor = page.next_cursor

    async def get(self, id: str) -> Message:
        return Message.from_dict(
            await self._t.request_json("GET", f"/v1/messages/{id}")
        )

    async def cancel(self, id: str) -> CancelResult:
        return CancelResult.from_dict(
            await self._t.request_json("DELETE", f"/v1/messages/{id}")
        )
