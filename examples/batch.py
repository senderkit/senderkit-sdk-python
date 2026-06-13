"""Batch send with per-item error handling.

Run: SENDERKIT_API_KEY=sk_test_... python examples/batch.py
"""

import os

from senderkit import SenderKit, TemplateSend

recipients = [f"user{i}@example.com" for i in range(50)]

with SenderKit(api_key=os.environ["SENDERKIT_API_KEY"]) as sk:
    requests = [
        TemplateSend(template="welcome", to=to, vars={"index": i})
        for i, to in enumerate(recipients)
    ]
    results = sk.send_batch(requests, concurrency=10, idempotency_key="welcome-batch-1")

    ok = sum(1 for r in results if r.ok)
    print(f"sent {ok}/{len(results)}")
    for r in results:
        if not r.ok:
            print("failed:", r.index, type(r.error).__name__, r.error)
