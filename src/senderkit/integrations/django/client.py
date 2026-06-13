"""Build and cache a :class:`~senderkit.SenderKit` from Django settings."""

from __future__ import annotations

from typing import Any, Dict, Optional

from ...client import DEFAULT_BASE_URL, DEFAULT_MAX_RETRIES, DEFAULT_TIMEOUT, SenderKit

_client: Optional[SenderKit] = None


def get_config() -> Dict[str, Any]:
    """Return the ``SENDERKIT`` settings dict (empty if unset)."""
    from django.conf import settings

    return dict(getattr(settings, "SENDERKIT", {}) or {})


def get_client() -> SenderKit:
    """Return a process-wide :class:`~senderkit.SenderKit` built from settings."""
    global _client
    if _client is None:
        config = get_config()
        api_key = config.get("API_KEY")
        if not api_key:
            from django.core.exceptions import ImproperlyConfigured

            raise ImproperlyConfigured("SENDERKIT['API_KEY'] is not set.")
        _client = SenderKit(
            api_key=api_key,
            base_url=config.get("BASE_URL", DEFAULT_BASE_URL),
            timeout=config.get("TIMEOUT", DEFAULT_TIMEOUT),
            max_retries=config.get("MAX_RETRIES", DEFAULT_MAX_RETRIES),
        )
    return _client


def reset_client() -> None:
    """Drop the cached client (useful in tests and after settings changes)."""
    global _client
    if _client is not None:
        _client.close()
    _client = None
