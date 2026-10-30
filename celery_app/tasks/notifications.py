"""Задачи для уведомлений."""

import asyncio
import logging
import smtplib
from collections.abc import Coroutine
from email.message import EmailMessage
from typing import Any

from sqlalchemy import select

from celery_app.celery import celery_app
from shared.core.db import get_session
from shared.core.settings import settings
from shared.models.booking import Booking
from shared.models.cafe_manager import CafeManager
from shared.models.user import User

logger = logging.getLogger(__name__)


@celery_app.task(name='tasks.send_sms')
def send_sms(phone: str, text: str) -> str:
    """Отправка SMS."""
    logger.info('SMS to %s: %s', phone, text)
    return f'SMS sent to {phone}'


@celery_app.task(name='tasks.send_email')
def send_email(email: str, subject: str, text: str) -> str:
    """Отправка email."""
    msg = EmailMessage()
    msg['From'] = settings.smtp_from
    msg['To'] = email
    msg['Subject'] = subject
    msg.set_content(text)

    if settings.smtp_use_ssl:
        server = smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port)
    else:
        server = smtplib.SMTP(settings.smtp_host, settings.smtp_port)
        server.starttls()

    server.login(settings.smtp_user, settings.smtp_password)
    server.sendmail(settings.smtp_from, [email], msg.as_string())
    server.quit()
    logger.info('Email sent to %s', email)
    return f'Email sent to {email}'


@celery_app.task(name='tasks.send_telegram')
def send_telegram(tg_id: str, text: str) -> str:
    """Отправка в Telegram (заглушка)."""
    logger.info('Telegram to %s: %s', tg_id, text)
    return f'Telegram sent to {tg_id}'


def _run[T](coro: Coroutine[Any, Any, T]) -> T:
    """Запускает async-корутину в sync-контексте Celery."""
    return asyncio.run(coro)


@celery_app.task(name='tasks.notify_booking_created')
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
            user = await session.get(User, booking.user_id)
            if user and user.email:
                send_email.delay(
                    email=user.email,
                    subject='Бронь создана',
                    text=(
                        f'Здравствуйте! Ваша бронь в кафе '
                        f'{booking.cafe_id} на {booking.booking_date} создана.'
                    ),
                )

            managers_result = await session.execute(
                select(User)
                .join(CafeManager, CafeManager.user_id == User.id)
                .where(
                    CafeManager.cafe_id == booking.cafe_id,
                    CafeManager.is_active.is_(True),
                    User.is_active.is_(True),
                ),
            )
            for manager in managers_result.scalars().all():
                if manager.email:
                    send_email.delay(
                        email=manager.email,
                        subject='Новая бронь в кафе',
                        text=(
                            f'Новая бронь #{booking.id} в кафе {booking.cafe_id} на {booking.booking_date}.'
                        ),
                    )
            return booking.id

    booking_id = _run(_notify())
    return f'Booking {booking_id} created notification sent'


@celery_app.task(name='tasks.notify_booking_updated')
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
            user = await session.get(User, booking.user_id)
            if user and user.email:
                send_email.delay(
                    email=user.email,
                    subject='Бронь обновлена',
                    text=(f'Ваша бронь #{booking.id} обновлена. Статус: {booking.status}.'),
                )

            managers_result = await session.execute(
                select(User)
                .join(CafeManager, CafeManager.user_id == User.id)
                .where(
                    CafeManager.cafe_id == booking.cafe_id,
                    CafeManager.is_active.is_(True),
                    User.is_active.is_(True),
                ),
            )
            for manager in managers_result.scalars().all():
                if manager.email:
                    send_email.delay(
                        email=manager.email,
                        subject='Бронь обновлена',
                        text=(
                            f'Бронь #{booking.id} в кафе '
                            f'{booking.cafe_id} обновлена (статус: {booking.status}).'
                        ),
                    )
            return booking.id

    booking_id = _run(_notify())
    return f'Booking {booking_id} updated notification sent'


@celery_app.task(name='tasks.notify_booking_reminder')
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
            return booking.id

    booking_id = _run(_notify())
    return f'Booking {booking_id} reminder sent'


@celery_app.task(name='tasks.notify_booking_cancelled')
def notify_booking_cancelled(booking_id: int) -> str:
    """Уведомление об отмене брони."""

    async def _notify() -> int:
        async with get_session() as session:
            result = await session.execute(
                select(Booking).where(Booking.id == booking_id),
            )
            booking = result.scalar_one_or_none()
            if booking is None:
                logger.warning('Booking %s not found', booking_id)
                return booking_id

            user = await session.get(User, booking.user_id)
            managers_result = await session.execute(
                select(User)
                .join(CafeManager, CafeManager.user_id == User.id)
                .where(
                    CafeManager.cafe_id == booking.cafe_id,
                    CafeManager.is_active.is_(True),
                    User.is_active.is_(True),
                ),
            )
            managers = managers_result.scalars().all()

            if user and user.email:
                send_email.delay(
                    email=user.email,
                    subject='Бронь отменена',
                    text=(
                        f'Ваша бронь #{booking.id} в кафе {booking.cafe_id} '
                        f'на {booking.booking_date} отменена.'
                    ),
                )

            for manager in managers:
                if manager.email:
                    send_email.delay(
                        email=manager.email,
                        subject='Бронь отменена',
                        text=(
                            f'Бронь #{booking.id} в кафе {booking.cafe_id} '
                            f'на {booking.booking_date} отменена.'
                        ),
                    )
            return booking.id

    booking_id = _run(_notify())
    return f'Booking {booking_id} cancelled notification sent'
