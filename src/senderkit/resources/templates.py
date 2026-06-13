"""The ``templates`` resource: list, get, and render."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .._http import AsyncTransport, Transport
from ..models import RenderResult, TemplateDetail, TemplateSummary


class Templates:
    """Synchronous template operations."""

    def __init__(self, transport: Transport) -> None:
        self._t = transport

    def list(self) -> List[TemplateSummary]:
        """Return every template in the workspace."""
        data = self._t.request_json("GET", "/v1/templates")
        items = data.get("data") or []
        return [TemplateSummary.from_dict(t) for t in items]

    def get(self, slug: str) -> TemplateDetail:
        """Return a template's detail, including its current published version."""
        return TemplateDetail.from_dict(
            self._t.request_json("GET", f"/v1/templates/{slug}")
        )

    def render(
        self, slug: str, vars: Optional[Dict[str, Any]] = None
    ) -> RenderResult:
        """Render the published version with ``vars`` without sending."""
        return RenderResult.from_dict(
            self._t.request_json(
                "POST", f"/v1/templates/{slug}/render", body={"vars": vars or {}}
            )
        )


class AsyncTemplates:
    """Asynchronous template operations."""

    def __init__(self, transport: AsyncTransport) -> None:
        self._t = transport

    async def list(self) -> List[TemplateSummary]:
        data = await self._t.request_json("GET", "/v1/templates")
        items = data.get("data") or []
        return [TemplateSummary.from_dict(t) for t in items]

    async def get(self, slug: str) -> TemplateDetail:
        return TemplateDetail.from_dict(
            await self._t.request_json("GET", f"/v1/templates/{slug}")
        )

    async def render(
        self, slug: str, vars: Optional[Dict[str, Any]] = None
    ) -> RenderResult:
        return RenderResult.from_dict(
            await self._t.request_json(
                "POST", f"/v1/templates/{slug}/render", body={"vars": vars or {}}
            )
        )
