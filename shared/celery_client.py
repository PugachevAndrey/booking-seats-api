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


def send_notification(task_name: str, booking_id: int, **kwargs: Any) -> str | None:
    """Отправить задачу в Celery, не блокируя API. Возвращает ID задачи."""
    try:
        result = celery_client.send_task(
            task_name,
            args=[booking_id],
            retry=False,
            connection_timeout=1,
            **kwargs,
        )
        return result.id
    except Exception as exc:
        logger.warning(
            'Не удалось отправить %s для брони %s: %s',
            task_name,
            booking_id,
            exc,
        )
        return None


def revoke_task(task_id: str | None) -> None:
    """Отзывает задачу Celery (например, напоминание при отмене брони)."""
    if not task_id:
        return
    try:
        celery_client.control.revoke(task_id, terminate=False)
        logger.info('Задача %s отозвана', task_id)
    except Exception as exc:
        logger.warning('Не удалось отозвать задачу %s: %s', task_id, exc)


celery_client.conf.update(
    task_serializer='json',
    accept_content=['json'],
    timezone='UTC',
    enable_utc=True,
    # Клиент тоже публикует событие "task sent" — нужно для Flower
    task_send_sent_event=True,
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
