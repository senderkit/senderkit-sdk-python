"""Django integration for SenderKit.

Configure via a ``SENDERKIT`` dict in settings::

    SENDERKIT = {
        "API_KEY": env("SENDERKIT_API_KEY"),
        "BASE_URL": "https://api.senderkit.com",   # optional
        "TIMEOUT": 30.0,                             # optional, seconds
        "MAX_RETRIES": 2,                            # optional
        "WEBHOOK_SECRET": env("SENDERKIT_WEBHOOK_SECRET"),  # for webhooks
    }

Use it three ways:

- ``EMAIL_BACKEND = "senderkit.integrations.django.EmailBackend"`` to route
  ``django.core.mail`` through SenderKit.
- ``get_client()`` for a configured :class:`~senderkit.SenderKit` instance.
- ``@senderkit_webhook`` to verify and dispatch inbound webhooks.
"""

from .backends import EmailBackend
from .client import get_client, reset_client
from .views import senderkit_webhook

__all__ = ["EmailBackend", "get_client", "reset_client", "senderkit_webhook"]
