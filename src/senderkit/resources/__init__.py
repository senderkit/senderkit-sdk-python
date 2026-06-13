"""Resource namespaces exposed on the client (``client.messages``, ``client.templates``)."""

from .messages import AsyncMessages, Messages
from .templates import AsyncTemplates, Templates

__all__ = ["Messages", "AsyncMessages", "Templates", "AsyncTemplates"]
