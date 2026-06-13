"""Django configuration snippet for the SenderKit integration.

Add these to your project's ``settings.py``, then send mail as usual with
``django.core.mail`` — it routes through SenderKit. For webhooks, wire the
``senderkit_webhook`` decorator into a view (see below).
"""

import os

# --- settings.py ---------------------------------------------------------- #
EMAIL_BACKEND = "senderkit.integrations.django.EmailBackend"

SENDERKIT = {
    "API_KEY": os.environ["SENDERKIT_API_KEY"],
    "BASE_URL": "https://api.senderkit.com",  # optional
    "TIMEOUT": 30.0,  # optional, seconds
    "MAX_RETRIES": 2,  # optional
    "WEBHOOK_SECRET": os.environ.get("SENDERKIT_WEBHOOK_SECRET"),
}

# --- usage in code -------------------------------------------------------- #
# from django.core.mail import send_mail
# send_mail("Hi", "Welcome aboard", "from@example.com", ["user@example.com"])
#
# Or send a template directly:
# from senderkit.integrations.django import get_client
# get_client().send("welcome", "user@example.com", vars={"name": "Ada"})

# --- webhook view (views.py) ---------------------------------------------- #
# from django.http import HttpResponse
# from senderkit.integrations.django import senderkit_webhook
#
# @senderkit_webhook
# def senderkit_events(request, event):
#     print(event.type, event.payload)
#     return HttpResponse(status=204)
#
# urlpatterns = [path("webhooks/senderkit", senderkit_events)]
