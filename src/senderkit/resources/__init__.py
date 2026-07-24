"""Resource namespaces exposed on the client (``client.messages``, ``client.templates``,
``client.inbound``)."""

from .inbound import AsyncInbound, Inbound
from .messages import AsyncMessages, Messages
from .templates import AsyncTemplates, Templates

__all__ = [
    "Messages",
    "AsyncMessages",
    "Templates",
    "AsyncTemplates",
    "Inbound",
    "AsyncInbound",
]
