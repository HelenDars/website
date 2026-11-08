"""Celery: фоновые задачи и расписание загрузок."""
from celery import Celery

from app.config import get_settings

settings = get_settings()

celery_app = Celery("nordis", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.update(
    timezone=settings.nordis_timezone,
    enable_utc=True,
    task_acks_late=True,
    # Расписание появится вместе с коннекторами (спринт 3):
    # CRM, Kaspi, Meta — каждые 60 минут; показатели — к 07:30; брифинг — 08:00.
    beat_schedule={},
)


@celery_app.task(name="nordis.ping")
def ping() -> str:
    return "pong"
