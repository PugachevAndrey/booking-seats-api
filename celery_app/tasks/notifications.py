"""Задачи для уведомлений."""

import asyncio
import logging
from collections.abc import Coroutine
from typing import Any

from sqlalchemy import select

from celery_app.celery import celery_app
from shared.core.db import get_session
from shared.models.booking import Booking

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


def _run[T](coro: Coroutine[Any, Any, T]) -> T:
    """Запускает async-корутину в sync-контексте Celery."""
    return asyncio.run(coro)


@celery_app.task
def notify_booking_created(booking_id: int) -> str:
    """Уведомление о создании брони."""

    async def _notify() -> int:
        async with get_session() as session:
            result = await session.execute(
                select(Booking).where(Booking.id == booking_id),
            )
            booking = result.scalar_one_or_none()
            if booking is None:
                logger.warning('Booking %s not found', booking_id)
                return booking_id
            logger.info(
                'Booking %s created: user_id=%s, cafe_id=%s, date=%s',
                booking.id,
                booking.user_id,
                booking.cafe_id,
                booking.booking_date,
            )
            # TODO: отправить SMS/email/Telegram
            return booking.id

    booking_id = _run(_notify())
    return f'Booking {booking_id} created notification sent'


@celery_app.task
def notify_booking_updated(booking_id: int) -> str:
    """Уведомление об изменении брони."""

    async def _notify() -> int:
        async with get_session() as session:
            result = await session.execute(
                select(Booking).where(Booking.id == booking_id),
            )
            booking = result.scalar_one_or_none()
            if booking is None:
                logger.warning('Booking %s not found', booking_id)
                return booking_id
            logger.info(
                'Booking %s updated: status=%s',
                booking.id,
                booking.status,
            )
            # TODO: отправить уведомление
            return booking.id

    booking_id = _run(_notify())
    return f'Booking {booking_id} updated notification sent'


@celery_app.task
def notify_booking_reminder(booking_id: int) -> str:
    """Напоминание клиенту о брони."""

    async def _notify() -> int:
        async with get_session() as session:
            result = await session.execute(
                select(Booking).where(Booking.id == booking_id),
            )
            booking = result.scalar_one_or_none()
            if booking is None:
                logger.warning('Booking %s not found', booking_id)
                return booking_id
            logger.info(
                'Booking %s reminder: user_id=%s, date=%s',
                booking.id,
                booking.user_id,
                booking.booking_date,
            )
            # TODO: отправить напоминание
            return booking.id

    booking_id = _run(_notify())
    return f'Booking {booking_id} reminder sent'
