"""Бизнес-логика бронирований."""

from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from repositories.booking import booking_crud
from repositories.cafe import cafe_crud
from repositories.slot import slot_crud
from repositories.table import table_crud
from schemas.booking import BookingUpdate
from shared.core.enums import BookingStatus
from shared.core.errors import (
    ConflictError,
    NotFoundError,
    PermissionDeniedError,
    ValidationError,
)
from shared.models.booking import Booking
from validators import validate_booking_date, validate_booking_note

from .access import (
    ROLE_ADMIN,
    ensure_cafe_access,
    ensure_owner_or_staff,
    is_staff,
)
from .user import get_user

BOOKING_EDITABLE_FIELDS = frozenset(
    {'guest_number', 'note', 'status', 'booking_date', 'tables_slots'},
)
GUEST_NUMBER_MIN = 1
BUYABLE_STATUSES = (
    BookingStatus.BOOKING.value,
    BookingStatus.COMPLETED.value,
)
SLOT_BUSY_MESSAGE = 'Стол занят в выбранном слоте на эту дату.'


async def get_booking(session: AsyncSession, booking_id: int) -> Booking:
    """Возвращает активное бронирование по ID."""
    booking = await booking_crud.get(session=session, obj_id=booking_id)
    if booking is None or not booking.is_active:
        raise NotFoundError(f'Бронирование {booking_id} не найдено.')
    return booking


async def get_bookings(
    session: AsyncSession,
    actor_id: int,
    actor_role: str,
    actor_cafe_id: int | None,
    booking_date: date | None = None,
) -> list[Booking]:
    """Возвращает активные бронирования согласно роли и дате."""
    if not is_staff(actor_role):
        bookings = await booking_crud.get_by_user(
            session=session,
            user_id=actor_id,
            booking_date=booking_date,
        )
    elif actor_role == ROLE_ADMIN:
        bookings = await booking_crud.get_multi(session=session)
        if booking_date is not None:
            bookings = [
                item
                for item in bookings
                if item.booking_date == booking_date
            ]
    else:
        if actor_cafe_id is None:
            return []
        bookings = await booking_crud.get_by_cafe(
            session=session,
            cafe_id=actor_cafe_id,
            booking_date=booking_date,
        )

    return sorted(
        (booking for booking in bookings if booking.is_active),
        key=lambda booking: booking.booking_date,
    )


async def is_slot_busy(
    session: AsyncSession,
    table_id: int,
    slot_id: int,
    booking_date: date,
    exclude_booking_id: int | None = None,
) -> bool:
    """Проверяет, занят ли стол в слоте на дату брони."""
    return await booking_crud.is_slot_busy(
        session=session,
        table_id=table_id,
        slot_id=slot_id,
        booking_date=booking_date,
        statuses=BUYABLE_STATUSES,
        exclude_booking_id=exclude_booking_id,
    )


async def _ensure_cafe_active(
    session: AsyncSession,
    cafe_id: int,
) -> None:
    """Проверяет, что кафе существует и активно."""
    cafe = await cafe_crud.get(session=session, obj_id=cafe_id)
    if cafe is None or not cafe.is_active:
        raise NotFoundError(f'Кафе {cafe_id} не найдено.')


async def _ensure_table_and_slot_in_cafe(
    session: AsyncSession,
    table_id: int,
    slot_id: int,
    cafe_id: int,
) -> None:
    """Проверяет, что стол и слот принадлежат кафе."""
    table = await table_crud.get(session=session, obj_id=table_id)
    if table is None or not table.is_active:
        raise NotFoundError(f'Стол {table_id} не найден.')
    if table.cafe_id != cafe_id:
        raise ValidationError('Стол не принадлежит указанному кафе.')

    slot = await slot_crud.get(session=session, obj_id=slot_id)
    if slot is None or not slot.is_active:
        raise NotFoundError(f'Слот {slot_id} не найден.')
    if slot.cafe_id != cafe_id:
        raise ValidationError('Слот не принадлежит указанному кафе.')


async def _ensure_pairs_free(
    session: AsyncSession,
    pairs: list[tuple[int, int]],
    cafe_id: int,
    booking_date: date,
    exclude_booking_id: int | None = None,
) -> None:
    """Проверяет, что столы и слоты принадлежат кафе и свободны."""
    await _ensure_cafe_active(session, cafe_id)

    for table_id, slot_id in pairs:
        await _ensure_table_and_slot_in_cafe(
            session,
            table_id,
            slot_id,
            cafe_id,
        )
        if await is_slot_busy(
            session,
            table_id,
            slot_id,
            booking_date,
            exclude_booking_id=exclude_booking_id,
        ):
            raise ConflictError(SLOT_BUSY_MESSAGE)


async def _ensure_date_is_free(
    session: AsyncSession,
    booking_id: int,
    new_date: date,
) -> None:
    """Проверяет, что на новую дату все столы брони свободны."""
    links = await booking_crud.get_active_links(
        session=session,
        booking_id=booking_id,
    )
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


def _normalize_pairs(tables_slots: Any) -> list[tuple[int, int]]:
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


def _as_status(value: Any) -> BookingStatus:
    """Приводит значение к BookingStatus."""
    if isinstance(value, BookingStatus):
        return value
    return BookingStatus(value)


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
    if (
        _as_status(changes['status']) is BookingStatus.COMPLETED
        and booking.booking_date > date.today()
    ):
        raise ValidationError('Нельзя завершить бронь на будущую дату.')


def _validate_guest_number(guest_number: int) -> None:
    """Проверяет количество гостей."""
    if guest_number < GUEST_NUMBER_MIN:
        raise ValidationError(
            'Количество гостей должно быть положительным числом.',
        )


def _validate_changes(
    booking: Booking,
    changes: dict[str, Any],
    actor_role: str,
) -> None:
    """Проверяет изменяемые поля бронирования."""
    if 'status' in changes:
        changes['status'] = _as_status(changes['status'])
        _validate_status_change(booking, changes, actor_role)
    if 'booking_date' in changes:
        validate_booking_date(changes['booking_date'])
    if 'guest_number' in changes:
        _validate_guest_number(changes['guest_number'])
    if 'note' in changes:
        validate_booking_note(changes['note'])


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
        raise ValidationError('Клиент может бронировать только для себя.')

    await get_user(session, user_id)

    validate_booking_date(booking_date)
    _validate_guest_number(guest_number)
    validate_booking_note(note)

    pairs = _normalize_pairs(tables_slots)
    if not pairs:
        raise ValidationError('Нужно указать хотя бы один стол и слот.')

    now = datetime.now(tz=timezone.utc)
    if booking_date == now.date():
        for _, slot_id in pairs:
            slot = await slot_crud.get(session=session, obj_id=slot_id)
            if (
                slot is not None
                and slot.start_time is not None
                and slot.start_time <= now.time()
            ):
                raise ValidationError(
                    'Нельзя бронировать на прошедшее время.',
                )

    await _ensure_pairs_free(session, pairs, cafe_id, booking_date)

    booking = await booking_crud.create_from_dict(
        session=session,
        data={
            'user_id': user_id,
            'cafe_id': cafe_id,
            'guest_number': guest_number,
            'note': note or '',
            'status': BookingStatus.BOOKING.value,
            'booking_date': booking_date,
        },
    )

    await booking_crud.create_links(
        session=session,
        booking_id=booking.id,
        pairs=pairs,
    )
    return booking


async def update_booking(
    session: AsyncSession,
    actor_id: int,
    actor_role: str,
    actor_cafe_id: int | None,
    booking_id: int,
    **fields: Any,
) -> Booking:
    """Обновляет поля бронирования, при необходимости — столы и слоты."""
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

    pairs: list[tuple[int, int]] | None = None
    if 'tables_slots' in changes:
        pairs = _normalize_pairs(changes.pop('tables_slots'))
        if not pairs:
            raise ValidationError(
                'Нужно указать хотя бы один стол и слот.',
            )

    _validate_changes(booking, changes, actor_role)

    new_date = changes.get('booking_date', booking.booking_date)

    if pairs is not None:
        await _ensure_pairs_free(
            session,
            pairs,
            booking.cafe_id,
            new_date,
            exclude_booking_id=booking_id,
        )
    elif new_date != booking.booking_date:
        await _ensure_date_is_free(session, booking_id, new_date)

    if changes:
        booking = await booking_crud.update(
            session=session,
            db_obj=booking,
            obj_in=BookingUpdate(**changes),
        )

    if pairs is not None:
        await booking_crud.replace_links(
            session=session,
            booking_id=booking_id,
            pairs=pairs,
        )

    return booking


async def delete_booking(
    session: AsyncSession,
    actor_id: int,
    actor_role: str,
    actor_cafe_id: int | None,
    booking_id: int,
) -> None:
    """Мягко удаляет бронирование и его связки."""
    booking = await get_booking(session, booking_id)
    ensure_owner_or_staff(
        booking.user_id,
        actor_id,
        actor_role,
        actor_cafe_id,
        booking.cafe_id,
    )

    status = booking.status
    if _as_status(status) is not BookingStatus.COMPLETED:
        status = BookingStatus.CANCELLED.value

    await booking_crud.update(
        session=session,
        db_obj=booking,
        obj_in=BookingUpdate(is_active=False, status=status),
    )
    await booking_crud.deactivate_links(
        session=session,
        booking_id=booking_id,
    )


async def user_has_booking_in_cafe(
    session: AsyncSession,
    user_id: int,
    cafe_id: int,
) -> bool:
    """Проверяет, есть ли у пользователя бронирования в заданном кафе."""
    return await booking_crud.exists_for_user_in_cafe(
        session=session,
        user_id=user_id,
        cafe_id=cafe_id,
    )
