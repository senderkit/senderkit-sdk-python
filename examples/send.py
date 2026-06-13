"""Send a templated message (sync). Run: SENDERKIT_API_KEY=sk_test_... python examples/send.py"""

import os

from senderkit import SenderKit

with SenderKit(api_key=os.environ["SENDERKIT_API_KEY"]) as sk:
    print("mode:", sk.mode)

    result = sk.send(
        "welcome",
        "user@example.com",
        vars={"name": "Ada"},
        metadata={"userId": "usr_123"},
    )
    print("queued:", result.id, result.status, "livemode=", result.livemode)
