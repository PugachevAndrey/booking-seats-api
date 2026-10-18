"""Задачи для уведомлений."""
import logging

from core.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task
def send_sms(phone: str, text: str) -> str:
    """Отправка SMS."""
    logger.info('SMS to %s: %s', phone, text)
    # TODO: интеграция с SMS-провайдером
    return f'SMS sent to {phone}'


@celery_app.task
def send_email(email: str, subject: str, text: str) -> str:
    """Отправка email."""
    logger.info('Email to %s: %s', email, subject)
    # TODO: интеграция с SMTP
    return f'Email sent to {email}'


@celery_app.task
def send_telegram(tg_id: str, text: str) -> str:
    """Отправка в Telegram."""
    logger.info('Telegram to %s: %s', tg_id, text)
    # TODO: интеграция с Telegram Bot API
    return f'Telegram sent to {tg_id}'


@celery_app.task
def notify_booking_created(booking_id: int) -> str:
    """Уведомление о создании брони (SMS + email + Telegram)."""
    logger.info('Booking %s created notification', booking_id)
    # TODO: получить бронь из БД, отправить SMS/email/Telegram
    return f'Booking {booking_id} created notification sent'


@celery_app.task
def notify_booking_updated(booking_id: int) -> str:
    """Уведомление об изменении брони."""
    logger.info('Booking %s updated notification', booking_id)
    return f'Booking {booking_id} updated notification sent'


@celery_app.task
def notify_booking_reminder(booking_id: int) -> str:
    """Напоминание клиенту о брони."""
    logger.info('Booking %s reminder', booking_id)
    return f'Booking {booking_id} reminder sent'
