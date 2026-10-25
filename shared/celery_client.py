"""Клиент Celery для API (только отправка задач)."""

import logging
from typing import Any

from celery import Celery

from shared.core.settings import settings

logger = logging.getLogger(__name__)

celery_client = Celery(
    'booking_tasks_client',
    broker=settings.rabbitmq_url,
    backend=None,
)


def send_notification(task_name: str, booking_id: int, **kwargs: Any) -> None:
    """Отправить задачу в Celery, не блокируя API. Логирует при недоступном брокере."""
    try:
        celery_client.send_task(
            task_name,
            args=[booking_id],
            retry=False,
            connection_timeout=1,
            **kwargs,
        )
    except Exception as exc:
        logger.warning(
            'Не удалось отправить %s для брони %s: %s',
            task_name,
            booking_id,
            exc,
        )


celery_client.conf.update(
    task_serializer='json',
    accept_content=['json'],
    timezone='UTC',
    enable_utc=True,
    task_routes={
        'tasks.notify_*': {'queue': 'notifications'},
        'tasks.send_*': {'queue': 'notifications'},
    },
    broker_transport_options={
        'max_retries': 0,
        'interval_start': 0,
        'interval_step': 0,
        'interval_max': 0,
    },
)
