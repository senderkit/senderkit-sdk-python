"""Flask integration for SenderKit.

    from flask import Flask, request
    from senderkit.integrations.flask import SenderKitFlask

    app = Flask(__name__)
    app.config["SENDERKIT_API_KEY"] = "sk_test_..."
    app.config["SENDERKIT_WEBHOOK_SECRET"] = "whsec_..."
    senderkit = SenderKitFlask(app)        # or SenderKitFlask().init_app(app)

    @app.post("/welcome")
    def welcome():
        senderkit.client.send("welcome", "user@example.com")
        return "", 204

    @app.post("/webhooks/senderkit")
    def hook():
        event = senderkit.verify_webhook(request)   # aborts 400 on bad signature
        return {"type": event.type}

Config keys: ``SENDERKIT_API_KEY`` (required), ``SENDERKIT_BASE_URL``,
``SENDERKIT_TIMEOUT``, ``SENDERKIT_MAX_RETRIES``, ``SENDERKIT_WEBHOOK_SECRET``.
"""

from __future__ import annotations

from typing import Any, Optional

from ..client import (
    DEFAULT_BASE_URL,
    DEFAULT_MAX_RETRIES,
    DEFAULT_TIMEOUT,
    SenderKit,
)
from ..errors import SignatureVerificationError
from ..webhooks import DEFAULT_TOLERANCE_SECONDS, WebhookEvent, WebhookVerifier


class SenderKitFlask:
    """Flask extension exposing a configured :class:`~senderkit.SenderKit`."""

    def __init__(self, app: Optional[Any] = None) -> None:
        self._client: Optional[SenderKit] = None
        self._app: Optional[Any] = None
        if app is not None:
            self.init_app(app)

    def init_app(self, app: Any) -> None:
        app.config.setdefault("SENDERKIT_BASE_URL", DEFAULT_BASE_URL)
        app.config.setdefault("SENDERKIT_TIMEOUT", DEFAULT_TIMEOUT)
        app.config.setdefault("SENDERKIT_MAX_RETRIES", DEFAULT_MAX_RETRIES)
        app.config.setdefault("SENDERKIT_WEBHOOK_SECRET", None)
        app.extensions = getattr(app, "extensions", {})
        app.extensions["senderkit"] = self
        self._app = app

        def _teardown(exc: Any = None) -> None:  # pragma: no cover - lifecycle hook
            if self._client is not None:
                self._client.close()
                self._client = None

        app.teardown_appcontext(_teardown)

    @property
    def client(self) -> SenderKit:
        """The lazily-built, cached SenderKit client for the configured app."""
        if self._client is None:
            config = self._config()
            api_key = config.get("SENDERKIT_API_KEY")
            if not api_key:
                raise RuntimeError("SENDERKIT_API_KEY is not configured.")
            self._client = SenderKit(
                api_key=api_key,
                base_url=config["SENDERKIT_BASE_URL"],
                timeout=config["SENDERKIT_TIMEOUT"],
                max_retries=config["SENDERKIT_MAX_RETRIES"],
            )
        return self._client

    def verify_webhook(
        self,
        request: Any,
        *,
        secret: Optional[str] = None,
        tolerance: int = DEFAULT_TOLERANCE_SECONDS,
    ) -> WebhookEvent:
        """Verify the request's signature; abort with HTTP 400 on failure."""
        signing_secret = secret or self._config().get("SENDERKIT_WEBHOOK_SECRET")
        try:
            return WebhookVerifier(signing_secret).verify(
                request.get_data(),
                request.headers.get("X-SenderKit-Signature", ""),
                tolerance=tolerance,
                event_type=request.headers.get("X-SenderKit-Event"),
                delivery_id=request.headers.get("X-SenderKit-Delivery"),
            )
        except SignatureVerificationError as exc:
            from flask import abort

            abort(400, description=str(exc))

    def _config(self) -> Any:
        if self._app is not None:
            return self._app.config
        from flask import current_app

        return current_app.config
