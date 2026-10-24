"""Задачи Celery."""
from celery_app.tasks.notifications import (
    notify_booking_created,
    notify_booking_reminder,
    notify_booking_updated,
    send_email,
    send_sms,
    send_telegram,
)

__all__ = [
    'notify_booking_created',
    'notify_booking_reminder',
    'notify_booking_updated',
    'send_email',
    'send_sms',
    'send_telegram',
]
