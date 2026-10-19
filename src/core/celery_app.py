"""Настройка Celery."""
from celery import Celery

from core.settings import settings

celery_app = Celery(
    'booking_tasks',
    broker=settings.rabbitmq_url,
    backend=settings.rabbitmq_url,
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_routes={
        'tasks.notify_*': {'queue': 'notifications'},
        'tasks.send_*': {'queue': 'notifications'},
    },
)
