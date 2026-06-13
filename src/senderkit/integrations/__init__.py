"""Framework integrations.

Each submodule imports its framework lazily, so installing the core SDK never
pulls in Django/FastAPI/Flask/Celery. Import the one you need:

    from senderkit.integrations.django import EmailBackend, get_client, senderkit_webhook
    from senderkit.integrations.fastapi import get_senderkit, webhook_verifier
    from senderkit.integrations.flask import SenderKitFlask
    from senderkit.integrations.celery import make_send_task
"""
