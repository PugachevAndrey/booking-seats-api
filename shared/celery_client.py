"""Клиент Celery для API (только отправка задач)."""

from celery import Celery

from shared.core.settings import settings

celery_client = Celery(
    'booking_tasks_client',
    broker=settings.rabbitmq_url,
    backend=None,
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
)
