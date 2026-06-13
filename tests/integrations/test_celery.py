import httpx
import respx
from celery import Celery

from senderkit import SenderKit
from senderkit.integrations.celery import make_send_task
from tests.helpers import API_KEY, BASE_URL


def _celery_app() -> Celery:
    app = Celery("test")
    app.conf.update(task_always_eager=True, task_eager_propagates=True)
    return app


@respx.mock
def test_send_task_runs_eagerly():
    queued = {"id": "msg_1", "status": "queued", "livemode": False}
    respx.post(f"{BASE_URL}/v1/send").mock(return_value=httpx.Response(202, json=queued))
    app = _celery_app()
    send = make_send_task(app, lambda: SenderKit(api_key=API_KEY, base_url=BASE_URL))

    result = send.delay("welcome", "user@example.com", vars={"name": "Ada"}).get()
    assert result == {"id": "msg_1", "status": "queued", "livemode": False}


def test_make_send_task_registers_named_task():
    app = _celery_app()
    make_send_task(app, lambda: SenderKit(api_key=API_KEY, base_url=BASE_URL), name="custom.send")
    assert "custom.send" in app.tasks
