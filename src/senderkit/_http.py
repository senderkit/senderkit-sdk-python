"""Internal HTTP transport: header construction, retries with backoff,
idempotency, timeout/network mapping, and error-to-exception translation.

Two thin transports — ``Transport`` (sync, ``httpx.Client``) and
``AsyncTransport`` (``httpx.AsyncClient``) — share all policy via the module
helpers below. Not part of the public API; the client and resources use it.
"""

from __future__ import annotations

import asyncio
import json
import random
import time
from typing import Any, Dict, Optional

import httpx

from . import errors
from ._version import VERSION

RETRY_BASE_MS = 250
RETRY_CAP_MS = 5_000


def _is_retryable(status: int) -> bool:
    """429 and 5xx (except 501 Not Implemented) are worth retrying."""
    return status == 429 or (500 <= status < 600 and status != 501)


def _build_headers(
    api_key: str,
    idempotency_key: Optional[str],
    extra: Optional[Dict[str, str]],
) -> Dict[str, str]:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
        "User-Agent": f"senderkit-python/{VERSION}",
    }
    if idempotency_key:
        headers["Idempotency-Key"] = idempotency_key
    if extra:
        headers.update(extra)
    return headers


def _parse_retry_after(response: httpx.Response) -> Optional[float]:
    value = response.headers.get("retry-after")
    if not value:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _backoff_seconds(attempt: int, retry_after: Optional[float]) -> float:
    """Full-jitter exponential backoff, capped at ``RETRY_CAP_MS``.

    When the server sent ``Retry-After`` we wait at least that long (also capped),
    so we never hammer ahead of an explicit instruction.
    """
    cap = RETRY_CAP_MS / 1000
    ceiling = min(RETRY_CAP_MS, RETRY_BASE_MS * (2**attempt)) / 1000
    jitter = random.uniform(0, ceiling)
    if retry_after is not None:
        return min(max(retry_after, jitter), cap)
    return jitter


def _clean_query(query: Optional[Dict[str, Any]]) -> Optional[Dict[str, str]]:
    if not query:
        return None
    return {k: str(v) for k, v in query.items() if v is not None}


def _raise_for_status(response: httpx.Response) -> None:
    status = response.status_code
    if 200 <= status < 300:
        return

    code: Optional[str] = None
    message: Optional[str] = None
    issues: Any = None
    try:
        body = response.json()
        err = body.get("error") if isinstance(body, dict) else None
        if isinstance(err, dict):
            code = err.get("code")
            message = err.get("message")
            issues = err.get("issues")
    except (ValueError, json.JSONDecodeError):
        pass

    message = message or f"HTTP {status}"
    request_id = response.headers.get("x-request-id")

    if status in (401, 403):
        raise errors.AuthenticationError(
            message, status=status, code=code, issues=issues, request_id=request_id
        )
    if status in (400, 422):
        raise errors.ValidationError(
            message, status=status, code=code, issues=issues, request_id=request_id
        )
    if status == 402:
        raise errors.PaymentRequiredError(
            message, status=status, code=code, issues=issues, request_id=request_id
        )
    if status == 409:
        raise errors.ConflictError(
            message, status=status, code=code, issues=issues, request_id=request_id
        )
    if status == 429:
        raise errors.RateLimitError(
            message,
            status=status,
            code=code,
            issues=issues,
            request_id=request_id,
            retry_after=_parse_retry_after(response),
        )
    raise errors.APIError(
        message, status=status, code=code, issues=issues, request_id=request_id
    )


class _BaseTransport:
    def __init__(self, api_key: str, base_url: str, max_retries: int) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._max_retries = max_retries

    def _url(self, path: str) -> str:
        return self._base_url + (path if path.startswith("/") else f"/{path}")

    def _prepare(
        self,
        body: Optional[Dict[str, Any]],
        idempotency_key: Optional[str],
        headers: Optional[Dict[str, str]],
        accept: Optional[str],
    ) -> tuple[Dict[str, str], Optional[bytes]]:
        h = _build_headers(self._api_key, idempotency_key, headers)
        if accept:
            h["Accept"] = accept
        content: Optional[bytes] = None
        if body is not None:
            content = json.dumps(body).encode()
            h["Content-Type"] = "application/json"
        return h, content


class Transport(_BaseTransport):
    """Synchronous transport over ``httpx.Client``."""

    def __init__(
        self,
        api_key: str,
        base_url: str,
        timeout: float,
        max_retries: int,
        http_client: Optional[httpx.Client] = None,
    ) -> None:
        super().__init__(api_key, base_url, max_retries)
        self._owns_client = http_client is None
        self._client = http_client or httpx.Client(timeout=timeout)

    def request(
        self,
        method: str,
        path: str,
        *,
        query: Optional[Dict[str, Any]] = None,
        body: Optional[Dict[str, Any]] = None,
        idempotency_key: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        accept: Optional[str] = None,
    ) -> httpx.Response:
        url = self._url(path)
        h, content = self._prepare(body, idempotency_key, headers, accept)
        params = _clean_query(query)
        attempts = 1 + self._max_retries

        for attempt in range(attempts):
            try:
                response = self._client.request(
                    method, url, params=params, content=content, headers=h
                )
            except httpx.TimeoutException as exc:
                raise errors.TimeoutError(f"Request timed out: {exc}") from exc
            except httpx.RequestError as exc:
                if attempt < attempts - 1:
                    time.sleep(_backoff_seconds(attempt, None))
                    continue
                raise errors.NetworkError(f"Network error: {exc}") from exc

            if _is_retryable(response.status_code) and attempt < attempts - 1:
                time.sleep(_backoff_seconds(attempt, _parse_retry_after(response)))
                continue

            _raise_for_status(response)
            return response

        raise errors.NetworkError("Request failed after retries")  # pragma: no cover

    def request_json(self, method: str, path: str, **kwargs: Any) -> Dict[str, Any]:
        response = self.request(method, path, **kwargs)
        if not response.content:
            return {}
        data = response.json()
        return data if isinstance(data, dict) else {"data": data}

    def close(self) -> None:
        if self._owns_client:
            self._client.close()


class AsyncTransport(_BaseTransport):
    """Asynchronous transport over ``httpx.AsyncClient``."""

    def __init__(
        self,
        api_key: str,
        base_url: str,
        timeout: float,
        max_retries: int,
        http_client: Optional[httpx.AsyncClient] = None,
    ) -> None:
        super().__init__(api_key, base_url, max_retries)
        self._owns_client = http_client is None
        self._client = http_client or httpx.AsyncClient(timeout=timeout)

    async def request(
        self,
        method: str,
        path: str,
        *,
        query: Optional[Dict[str, Any]] = None,
        body: Optional[Dict[str, Any]] = None,
        idempotency_key: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        accept: Optional[str] = None,
    ) -> httpx.Response:
        url = self._url(path)
        h, content = self._prepare(body, idempotency_key, headers, accept)
        params = _clean_query(query)
        attempts = 1 + self._max_retries

        for attempt in range(attempts):
            try:
                response = await self._client.request(
                    method, url, params=params, content=content, headers=h
                )
            except httpx.TimeoutException as exc:
                raise errors.TimeoutError(f"Request timed out: {exc}") from exc
            except httpx.RequestError as exc:
                if attempt < attempts - 1:
                    await asyncio.sleep(_backoff_seconds(attempt, None))
                    continue
                raise errors.NetworkError(f"Network error: {exc}") from exc

            if _is_retryable(response.status_code) and attempt < attempts - 1:
                await asyncio.sleep(
                    _backoff_seconds(attempt, _parse_retry_after(response))
                )
                continue

            _raise_for_status(response)
            return response

        raise errors.NetworkError("Request failed after retries")  # pragma: no cover

    async def request_json(
        self, method: str, path: str, **kwargs: Any
    ) -> Dict[str, Any]:
        response = await self.request(method, path, **kwargs)
        if not response.content:
            return {}
        data = response.json()
        return data if isinstance(data, dict) else {"data": data}

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()
