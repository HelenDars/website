from app.worker import celery_app, ping


def test_worker_uses_almaty_timezone():
    assert celery_app.conf.timezone == "Asia/Almaty"


def test_ping_task_runs():
    assert ping.apply().get() == "pong"
