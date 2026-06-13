"""Send messages concurrently (async).

Run: SENDERKIT_API_KEY=sk_test_... python examples/send_async.py
"""

import asyncio
import os

from senderkit import AsyncSenderKit, EmailContent


async def main() -> None:
    async with AsyncSenderKit(api_key=os.environ["SENDERKIT_API_KEY"]) as sk:
        # Concurrent template + raw sends.
        template, raw = await asyncio.gather(
            sk.send("welcome", "user@example.com", vars={"name": "Ada"}),
            sk.send_raw(
                "user@example.com",
                EmailContent(subject="Hello", html="<p>Hi there</p>"),
            ),
        )
        print("template:", template.id)
        print("raw:", raw.id)

        # Auto-paginate the workspace's recent messages.
        async for message in sk.messages.aiter(limit=20):
            print(message.public_id, message.status)


asyncio.run(main())
