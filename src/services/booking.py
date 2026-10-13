"""Сервисные функции для работы с бронированиями."""

from datetime import datetime, time
from typing import Any

from models.booking import Booking
from models.booking_tables_slot import BookingTablesSlot
from models.slot import Slot
from models.table import Table
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .access import (
    ROLE_ADMIN,
    ensure_cafe_access,
    ensure_owner_or_staff,
    is_staff,
)
from .errors import ConflictError, NotFoundError, ValidationError


async def get_booking(session: AsyncSession, booking_id: int) -> Booking:
    """Возвращает активное бронирование по ID."""
    booking = await session.get(Booking, booking_id)
    if booking is None or not booking.is_active:
        raise NotFoundError(f'Бронирование {booking_id} не найдено.')
    return booking


async def get_bookings(
    session: AsyncSession,
    actor_id: int,
    actor_role: str,
    actor_cafe_id: int | None,
) -> list[Booking]:
    """Возвращает бронирования согласно роли."""
    query = select(Booking).where(Booking.is_active.is_(True))
    if not is_staff(actor_role):
        query = query.where(Booking.user_id == actor_id)
    elif actor_role != ROLE_ADMIN and actor_cafe_id is not None:
        query = query.where(Booking.cafe_id == actor_cafe_id)
    result = await session.execute(query.order_by(Booking.booking_date))
    return list(result.scalars().all())


async def is_slot_busy(
    session: AsyncSession,
    table_id: int,
    slot_id: int,
    booking_date: datetime,
    exclude_booking_id: int | None = None,
) -> bool:
    """Проверяет, занят ли стол в слоте на дату брони."""
    day_start = datetime.combine(booking_date.date(), time.min)
    day_end = datetime.combine(booking_date.date(), time.max)
    query = (
        select(BookingTablesSlot)
        .join(Booking, Booking.id == BookingTablesSlot.booking_id)
        .where(
            BookingTablesSlot.table_id == table_id,
            BookingTablesSlot.slot_id == slot_id,
            Booking.is_active.is_(True),
            Booking.booking_date.between(day_start, day_end),
        )
    )
    if exclude_booking_id is not None:
        query = query.where(Booking.id != exclude_booking_id)
    result = await session.execute(query)
    return result.first() is not None


async def _get_booking_link(
    session: AsyncSession,
    booking_id: int,
) -> BookingTablesSlot | None:
    """Возвращает связку стола и слота для брони."""
    result = await session.execute(
        select(BookingTablesSlot).where(
            BookingTablesSlot.booking_id == booking_id,
        ),
    )
    return result.scalar_one_or_none()


async def _ensure_table_and_slot_in_cafe(
    session: AsyncSession,
    table_id: int,
    slot_id: int,
    cafe_id: int,
) -> None:
    """Проверяет, что стол и слот принадлежат кафе."""
    table = await session.get(Table, table_id)
    if table is None or not table.is_active:
        raise NotFoundError(f'Стол {table_id} не найден.')
    if table.cafe_id != cafe_id:
        raise ValidationError('Стол не принадлежит указанному кафе.')

    slot = await session.get(Slot, slot_id)
    if slot is None or not slot.is_active:
        raise NotFoundError(f'Слот {slot_id} не найден.')
    if slot.cafe_id != cafe_id:
        raise ValidationError('Слот не принадлежит указанному кафе.')


async def create_booking(
    session: AsyncSession,
    actor_id: int,
    actor_role: str,
    actor_cafe_id: int | None,
    user_id: int,
    cafe_id: int,
    guest_number: int,
    note: str,
    status: str,
    booking_date: datetime,
    table_id: int,
    slot_id: int,
) -> Booking:
    """Создаёт бронирование и связывает стол со слотом."""
    if is_staff(actor_role):
        ensure_cafe_access(actor_role, actor_cafe_id, cafe_id)
    elif user_id != actor_id:
        raise ValidationError('Клиент может бронировать только для себя.')

    await _ensure_table_and_slot_in_cafe(session, table_id, slot_id, cafe_id)
    if await is_slot_busy(session, table_id, slot_id, booking_date):
        raise ConflictError('Стол занят в выбранном слоте на эту дату.')

    booking = Booking(
        user_id=user_id,
        cafe_id=cafe_id,
        guest_number=guest_number,
        note=note,
        status=status,
        booking_date=booking_date,
    )
    session.add(booking)
    await session.flush()

    link = BookingTablesSlot(
        booking_id=booking.id,
        table_id=table_id,
        slot_id=slot_id,
    )
    session.add(link)
    await session.flush()
    await session.refresh(booking)
    return booking


async def update_booking(
    session: AsyncSession,
    actor_id: int,
    actor_role: str,
    actor_cafe_id: int | None,
    booking_id: int,
    **fields: Any,
) -> Booking:
    """Обновляет поля бронирования с проверкой прав и занятости."""
    booking = await get_booking(session, booking_id)
    ensure_owner_or_staff(
        booking.user_id,
        actor_id,
        actor_role,
        actor_cafe_id,
        booking.cafe_id,
    )

    allowed = {'guest_number', 'note', 'status', 'booking_date'}
    new_date = fields.get('booking_date', booking.booking_date)
    if new_date != booking.booking_date:
        link = await _get_booking_link(session, booking_id)
        if link is not None and await is_slot_busy(
            session,
            link.table_id,
            link.slot_id,
            new_date,
            exclude_booking_id=booking_id,
        ):
            raise ConflictError('Стол занят в выбранном слоте на эту дату.')

    for name, value in fields.items():
        if name in allowed:
            setattr(booking, name, value)
    await session.flush()
    await session.refresh(booking)
    return booking


async def delete_booking(
    session: AsyncSession,
    actor_id: int,
    actor_role: str,
    actor_cafe_id: int | None,
    booking_id: int,
) -> None:
    """Мягко удаляет бронирование с проверкой прав."""
    booking = await get_booking(session, booking_id)
    ensure_owner_or_staff(
        booking.user_id,
        actor_id,
        actor_role,
        actor_cafe_id,
        booking.cafe_id,
    )
    booking.is_active = False
    await session.flush()
