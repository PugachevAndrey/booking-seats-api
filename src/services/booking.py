from datetime import date
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.booking import Booking
from models.booking_tables_slot import BookingTablesSlot
from models.cafe import Cafe
from models.slot import Slot
from models.table import Table
from validators import (
    validate_booking_date,
    validate_booking_guest_number,
    validate_booking_note,
    validate_booking_status,
)

from .access import (
    ROLE_ADMIN,
    ensure_cafe_access,
    ensure_owner_or_staff,
    is_staff,
)
from .user import get_user
from core.enums import BookingStatus
from core.errors import (
    ConflictError,
    NotFoundError,
    PermissionDeniedError,
    ValidationError,
)

BOOKING_EDITABLE_FIELDS = frozenset(
    {'guest_number', 'note', 'status', 'booking_date'},
)
BOOKING_STATUSES = tuple(status.value for status in BookingStatus)
BUYABLE_STATUSES = (
    BookingStatus.BOOKING.value,
    BookingStatus.COMPLETED.value,
)
SLOT_BUSY_MESSAGE = 'Стол занят в выбранном слоте на эту дату.'


async def get_booking(session: AsyncSession, booking_id: int) -> Booking:
    """Возвращает активное бронирование по ID."""
    booking = await session.get(Booking, booking_id)
    if booking is None or not booking.is_active:
        raise NotFoundError(
            f'Бронирование {booking_id} не найдено.',
        )
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
    elif actor_role != ROLE_ADMIN:
        if actor_cafe_id is None:
            return []
        query = query.where(Booking.cafe_id == actor_cafe_id)
    result = await session.execute(
        query.order_by(Booking.booking_date),
    )
    return list(result.scalars().all())


async def is_slot_busy(
    session: AsyncSession,
    table_id: int,
    slot_id: int,
    booking_date: date,
    exclude_booking_id: int | None = None,
) -> bool:
    """Проверяет, занят ли стол в слоте на дату брони."""
    query = (
        select(BookingTablesSlot)
        .join(
            Booking,
            Booking.id == BookingTablesSlot.booking_id,
        )
        .where(
            BookingTablesSlot.table_id == table_id,
            BookingTablesSlot.slot_id == slot_id,
            Booking.is_active.is_(True),
            Booking.status.in_(BUYABLE_STATUSES),
            Booking.booking_date == booking_date,
        )
    )
    if exclude_booking_id is not None:
        query = query.where(Booking.id != exclude_booking_id)
    result = await session.execute(query)
    return result.first() is not None


async def _get_booking_links(
    session: AsyncSession,
    booking_id: int,
) -> list[BookingTablesSlot]:
    """Возвращает связки столов и слотов для брони."""
    result = await session.execute(
        select(BookingTablesSlot)
        .where(BookingTablesSlot.booking_id == booking_id)
        .order_by(BookingTablesSlot.id),
    )
    return list(result.scalars().all())


async def _ensure_date_is_free(
    session: AsyncSession,
    booking_id: int,
    new_date: date,
) -> None:
    """Проверяет, что на новую дату все столы брони свободны."""
    links = await _get_booking_links(session, booking_id)
    if not links:
        raise ValidationError(
            'У бронирования не найдена связка стола и слота.',
        )
    for link in links:
        if await is_slot_busy(
            session,
            link.table_id,
            link.slot_id,
            new_date,
            exclude_booking_id=booking_id,
        ):
            raise ConflictError(SLOT_BUSY_MESSAGE)


async def _ensure_cafe_active(
    session: AsyncSession,
    cafe_id: int,
) -> None:
    """Проверяет, что кафе существует и активно."""
    cafe = await session.get(Cafe, cafe_id)
    if cafe is None or not cafe.is_active:
        raise NotFoundError(f'Кафе {cafe_id} не найдено.')


async def _ensure_table_and_slot_in_cafe(
    session: AsyncSession,
    table_id: int,
    slot_id: int,
    cafe_id: int,
) -> None:
    """Проверяет, что стол и слот принадлежат кафе."""
    cafe = await session.get(Cafe, cafe_id)
    if cafe is None or not cafe.is_active:
        raise NotFoundError(f'Кафе {cafe_id} не найдено.')

    table = await session.get(Table, table_id)
    if table is None or not table.is_active:
        raise NotFoundError(f'Стол {table_id} не найден.')
    if table.cafe_id != cafe_id:
        raise ValidationError(
            'Стол не принадлежит указанному кафе.',
        )

    slot = await session.get(Slot, slot_id)
    if slot is None or not slot.is_active:
        raise NotFoundError(f'Слот {slot_id} не найден.')
    if slot.cafe_id != cafe_id:
        raise ValidationError(
            'Слот не принадлежит указанному кафе.',
        )


def _normalize_pairs(
    tables_slots: Any,
) -> list[tuple[int, int]]:
    """Приводит пары стол/слот из схемы к списку кортежей."""
    pairs: list[tuple[int, int]] = []
    seen: set[tuple[int, int]] = set()
    for item in tables_slots or []:
        if isinstance(item, dict):
            table_id = item.get('table_id')
            slot_id = item.get('slot_id')
        else:
            table_id = getattr(item, 'table_id', None)
            slot_id = getattr(item, 'slot_id', None)
        if table_id is None or slot_id is None:
            raise ValidationError(
                'Для бронирования нужны table_id и slot_id.',
            )
        pair = (int(table_id), int(slot_id))
        if pair in seen:
            raise ValidationError('Стол и слот продублированы.')
        seen.add(pair)
        pairs.append(pair)
    return pairs


def _validate_status_change(
    booking: Booking,
    changes: dict[str, Any],
    actor_role: str,
) -> None:
    """Проверяет смену статуса бронирования."""
    if not is_staff(actor_role):
        raise PermissionDeniedError(
            'Менять статус бронирования может только персонал.',
        )
    validate_booking_status(changes['status'], BOOKING_STATUSES)
    if (
        changes['status'] == BookingStatus.COMPLETED.value
        and booking.booking_date > date.today()
    ):
        raise ValidationError(
            'Нельзя завершить бронь на будущую дату.',
        )


def _validate_changes(
    booking: Booking,
    changes: dict[str, Any],
    actor_role: str,
) -> None:
    """Проверяет изменяемые поля бронирования."""
    if 'status' in changes:
        _validate_status_change(booking, changes, actor_role)
    if 'booking_date' in changes:
        validate_booking_date(changes['booking_date'])
    if 'guest_number' in changes:
        validate_booking_guest_number(changes['guest_number'])
    if 'note' in changes:
        validate_booking_note(changes['note'])


def _apply_changes(
    booking: Booking,
    changes: dict[str, Any],
) -> None:
    """Применяет подготовленные изменения к модели."""
    for field_name, value in changes.items():
        setattr(booking, field_name, value)


async def create_booking(
    session: AsyncSession,
    actor_id: int,
    actor_role: str,
    actor_cafe_id: int | None,
    user_id: int,
    cafe_id: int,
    guest_number: int,
    note: str | None,
    booking_date: date,
    tables_slots: Any,
) -> Booking:
    """Создаёт бронирование и связывает столы со слотами."""
    if is_staff(actor_role):
        ensure_cafe_access(actor_role, actor_cafe_id, cafe_id)
    elif user_id != actor_id:
        raise ValidationError(
            'Клиент может бронировать только для себя.',
        )

    await get_user(session, user_id)

    validate_booking_date(booking_date)
    validate_booking_guest_number(guest_number)
    validate_booking_note(note)

    pairs = _normalize_pairs(tables_slots)
    if not pairs:
        raise ValidationError('Нужно указать хотя бы один стол и слот.')

    await _ensure_cafe_active(session, cafe_id)

    for table_id, slot_id in pairs:
        await _ensure_table_and_slot_in_cafe(
            session, table_id, slot_id, cafe_id,
        )
        if await is_slot_busy(
            session, table_id, slot_id, booking_date,
        ):
            raise ConflictError(SLOT_BUSY_MESSAGE)

    booking = Booking(
        user_id=user_id,
        cafe_id=cafe_id,
        guest_number=guest_number,
        note=note,
        status=BookingStatus.BOOKING.value,
        booking_date=booking_date,
    )
    session.add(booking)
    await session.flush()

    for table_id, slot_id in pairs:
        session.add(
            BookingTablesSlot(
                booking_id=booking.id,
                table_id=table_id,
                slot_id=slot_id,
            ),
        )
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

    unknown = set(fields) - BOOKING_EDITABLE_FIELDS
    if unknown:
        raise ValidationError(
            f'Поля нельзя изменить: {", ".join(sorted(unknown))}.',
        )

    changes = dict(fields)
    status_value = changes.get('status')
    if isinstance(status_value, BookingStatus):
        changes['status'] = status_value.value

    _validate_changes(booking, changes, actor_role)

    new_date = changes.get('booking_date', booking.booking_date)
    if new_date != booking.booking_date:
        await _ensure_date_is_free(session, booking_id, new_date)

    _apply_changes(booking, changes)

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
    if booking.status != BookingStatus.COMPLETED.value:
        booking.status = BookingStatus.CANCELLED.value
    await session.flush()
