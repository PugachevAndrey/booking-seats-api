"""Настройка Celery."""

from celery import Celery

from shared.core.settings import settings

celery_app = Celery(
    'booking_tasks',
    broker=settings.rabbitmq_url,
    backend=None,
    include=['celery_app.tasks.notifications'],
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
    worker_send_task_events=True,
    task_send_sent_event=True,
    worker_prefetch_multiplier=1,
    broker_connection_retry_on_startup=True,
)
