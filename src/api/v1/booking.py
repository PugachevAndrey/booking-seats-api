"""Роутер бронирований."""

from datetime import date, datetime, time, timedelta
from typing import Annotated
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, status

from api.v1.deps import DbSession, get_current_user
from schemas.booking import BookingCreate, BookingInfo, BookingUpdate
from services.booking import (
    create_booking,
    get_booking,
    get_bookings,
    save_reminder_task,
    update_booking,
)
from services.cafe_manager import get_manager_cafe_id
from services.slot import get_slot
from shared.celery_client import revoke_task, send_notification
from shared.core.enums import BookingStatus, UserRole
from shared.core.errors import PermissionDeniedError, ValidationError
from shared.models.booking import Booking
from shared.models.user import User

router = APIRouter(prefix='/booking', tags=['Бронирования'])


def _reminder_eta(booking_date: date, slot_start_time: time, minutes: int) -> datetime:
    """ETA напоминания: за 2 часа до начала брони (UTC)."""
    naive = datetime.combine(booking_date, slot_start_time)
    return naive.replace(tzinfo=ZoneInfo('UTC')) - timedelta(minutes=minutes)


def _booking_to_info(booking: Booking) -> BookingInfo:
    """Собирает BookingInfo; user, cafe, tables_slots через relationship."""
    return BookingInfo.model_validate(booking, from_attributes=True)


def _ensure_user_can_see(
    booking: Booking,
    current_user: User,
    manager_cafe_id: int | None,
) -> None:
    if current_user.role == UserRole.USER.value and booking.user_id != current_user.id:
        raise PermissionDeniedError('Нет прав на это бронирование.')
    if current_user.role == UserRole.MANAGER.value and booking.cafe_id != manager_cafe_id:
        raise PermissionDeniedError('Нет прав на это бронирование.')


@router.get('', response_model=list[BookingInfo], summary='Список бронирований')
async def list_bookings(
    session: DbSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[BookingInfo]:
    """Возвращает список бронирований."""
    actor_cafe_id = None
    if current_user.role == UserRole.MANAGER.value:
        actor_cafe_id = await get_manager_cafe_id(session, current_user.id)

    bookings = await get_bookings(
        session,
        actor_id=current_user.id,
        actor_role=current_user.role,
        actor_cafe_id=actor_cafe_id,
    )
    return [_booking_to_info(b) for b in bookings]


@router.post(
    '',
    response_model=BookingInfo,
    status_code=status.HTTP_201_CREATED,
    summary='Создание нового бронирования',
)
async def create_booking_endpoint(
    data: BookingCreate,
    session: DbSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> BookingInfo:
    """Создание бронирования."""
    actor_cafe_id = None
    if current_user.role == UserRole.MANAGER.value:
        actor_cafe_id = await get_manager_cafe_id(session, current_user.id)

    payload = data.model_dump(exclude_unset=True)
    booking = await create_booking(
        session=session,
        actor_id=current_user.id,
        actor_role=current_user.role,
        actor_cafe_id=actor_cafe_id,
        user_id=current_user.id,
        cafe_id=payload['cafe_id'],
        guest_number=payload['guest_number'],
        note=payload.get('note'),
        booking_date=payload['booking_date'],
        tables_slots=payload['tables_slots'],
    )
    send_notification('tasks.notify_booking_created', booking.id)

    remind_minutes = payload.get('remind_before_minutes', 60)
    slot_id = payload['tables_slots'][0]['slot_id']
    slot = await get_slot(session, slot_id)

    task_id = send_notification(
        'tasks.notify_booking_reminder',
        booking.id,
        eta=_reminder_eta(booking.booking_date, slot.start_time, remind_minutes),
    )
    if task_id:
        await save_reminder_task(session, booking.id, task_id)

    return _booking_to_info(booking)


@router.get(
    '/{booking_id}',
    response_model=BookingInfo,
    summary='Информация о бронировании по ID',
)
async def get_booking_by_id(
    booking_id: int,
    session: DbSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> BookingInfo:
    """Информация о бронировании."""
    booking = await get_booking(session, booking_id)

    manager_cafe_id = None
    if current_user.role == UserRole.MANAGER.value:
        manager_cafe_id = await get_manager_cafe_id(session, current_user.id)
    _ensure_user_can_see(booking, current_user, manager_cafe_id)

    return _booking_to_info(booking)


@router.patch(
    '/{booking_id}',
    response_model=BookingInfo,
    summary='Обновление бронирования по ID',
)
async def update_booking_by_id(
    booking_id: int,
    data: BookingUpdate,
    session: DbSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> BookingInfo:
    """Обновление информации о бронировании."""
    booking = await get_booking(session, booking_id)

    manager_cafe_id = None
    if current_user.role == UserRole.MANAGER.value:
        manager_cafe_id = await get_manager_cafe_id(session, current_user.id)
    _ensure_user_can_see(booking, current_user, manager_cafe_id)

    if booking.booking_date < date.today():
        raise ValidationError('Нельзя изменить прошедшее бронирование.')
    if booking.status == BookingStatus.ACTIVE:
        raise ValidationError('Нельзя изменить активное бронирование.')

    fields = data.model_dump(exclude_unset=True)

    old_task_id = booking.reminder_task_id
    fields = data.model_dump(exclude_unset=True)

    updated = await update_booking(
        session=session,
        actor_id=current_user.id,
        actor_role=current_user.role,
        actor_cafe_id=manager_cafe_id,
        booking_id=booking_id,
        **fields,
    )
    cancelled = updated.status == BookingStatus.CANCELED.value or updated.is_active is False

    if cancelled:
        send_notification('tasks.notify_booking_cancelled', updated.id)
        if old_task_id:
            revoke_task(old_task_id)
        await save_reminder_task(session, updated.id, None)
    else:
        send_notification('tasks.notify_booking_updated', updated.id)
        if 'booking_date' in fields or 'tables_slots' in fields:
            if old_task_id:
                revoke_task(old_task_id)
            slot = await get_slot(session, updated.tables_slots[0].slot_id)
            task_id = send_notification(
                'tasks.notify_booking_reminder',
                updated.id,
                eta=_reminder_eta(updated.booking_date, slot.start_time, updated.remind_before_minutes or 60),
            )
            if task_id:
                await save_reminder_task(session, updated.id, task_id)

    return _booking_to_info(updated)
