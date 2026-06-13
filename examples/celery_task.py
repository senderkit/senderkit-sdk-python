"""Celery task for retryable background sends.

Run a worker:
    pip install "senderkit[celery]" redis
    SENDERKIT_API_KEY=sk_test_... celery -A examples.celery_task worker -l info

Then enqueue from anywhere:
    from examples.celery_task import send_email
    send_email.delay("welcome", "user@example.com", vars={"name": "Ada"})
"""

import os

from celery import Celery

from senderkit import SenderKit
from senderkit.integrations.celery import make_send_task

celery_app = Celery("senderkit_example", broker="redis://localhost:6379/0")


def _client() -> SenderKit:
    return SenderKit(api_key=os.environ["SENDERKIT_API_KEY"])


# Rate limits, network errors, and timeouts are retried with exponential backoff.
send_email = make_send_task(celery_app, _client)
