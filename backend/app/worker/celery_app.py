"""
Celery application configuration.

Broker: Redis (CELERY_BROKER_URL)
Result backend: Redis (CELERY_RESULT_BACKEND)

Tasks autodiscovered from app.worker.tasks.
"""
from __future__ import annotations

from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "inklusifmath",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.worker.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Jakarta",
    enable_utc=True,
    # Retry config
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    # Result expiry: 24 hours
    result_expires=86400,
    # Rate limits
    task_default_rate_limit="10/m",
)
