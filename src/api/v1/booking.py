"""Роутер бронирований."""

from datetime import date, datetime, time, timedelta
from typing import Annotated
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.deps import get_current_user, get_db
from schemas.booking import BookingCreate, BookingInfo, BookingUpdate
from schemas.booking_tables_slot import BookingTableSlotShortInfo
from schemas.cafe import CafeShortInfo
from schemas.slot import TimeSlotShortInfo
from schemas.table import TableShortInfo
from schemas.user import UserShortInfo
from services.booking import (
    create_booking,
    get_booking,
    get_bookings,
    update_booking,
)
from services.cafe import get_cafe
from services.cafe_manager import get_manager_cafe_id
from services.slot import get_slot
from services.table import get_table
from services.user import get_user
from shared.celery_client import send_notification
from shared.core.enums import BookingStatus, UserRole
from shared.core.errors import PermissionDeniedError, ValidationError
from shared.models.booking import Booking
from shared.models.booking_tables_slot import BookingTablesSlot
from shared.models.user import User

router = APIRouter(prefix='/booking', tags=['Бронирования'])


def _reminder_eta(booking_date: date, slot_start_time: time) -> datetime:
    """ETA напоминания: за 2 часа до начала брони (UTC)."""
    naive = datetime.combine(booking_date, slot_start_time)
    return naive.replace(tzinfo=ZoneInfo('UTC')) - timedelta(hours=2)


async def _booking_to_info(session: AsyncSession, booking: Booking) -> BookingInfo:
    """Собирает BookingInfo с вложенными user, cafe, tables_slots."""
    user = await get_user(session, booking.user_id)
    cafe = await get_cafe(session, booking.cafe_id)

    links_result = await session.execute(
        select(BookingTablesSlot)
        .where(
            BookingTablesSlot.booking_id == booking.id,
        )
        .order_by(BookingTablesSlot.id),
    )
    links = list(links_result.scalars().all())

    tables_slots: list[BookingTableSlotShortInfo] = []
    for link in links:
        table = await get_table(session, link.table_id)
        slot = await get_slot(session, link.slot_id)
        tables_slots.append(
            BookingTableSlotShortInfo(
                table=TableShortInfo.model_validate(table, from_attributes=True),
                slot=TimeSlotShortInfo.model_validate(slot, from_attributes=True),
            ),
        )

    return BookingInfo(
        id=booking.id,
        user=UserShortInfo.model_validate(user, from_attributes=True),
        cafe=CafeShortInfo.model_validate(cafe, from_attributes=True),
        tables_slots=tables_slots,
        guest_number=booking.guest_number,
        note=booking.note,
        status=booking.status,
        booking_date=booking.booking_date,
        is_active=booking.is_active,
        created_at=booking.created_at,
        updated_at=booking.updated_at,
    )


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
    session: Annotated[AsyncSession, Depends(get_db)],
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
    return [await _booking_to_info(session, b) for b in bookings]


@router.post(
    '',
    response_model=BookingInfo,
    status_code=status.HTTP_201_CREATED,
    summary='Создание нового бронирования',
)
async def create_booking_endpoint(
    data: BookingCreate,
    session: Annotated[AsyncSession, Depends(get_db)],
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

    slot_id = payload['tables_slots'][0]['slot_id']
    slot = await get_slot(session, slot_id)
    send_notification(
        'tasks.notify_booking_reminder',
        booking.id,
        eta=_reminder_eta(booking.booking_date, slot.start_time),
    )

    return await _booking_to_info(session, booking)


@router.get(
    '/{booking_id}',
    response_model=BookingInfo,
    summary='Информация о бронировании по ID',
)
async def get_booking_by_id(
    booking_id: int,
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> BookingInfo:
    """Информация о бронировании."""
    booking = await get_booking(session, booking_id)

    manager_cafe_id = None
    if current_user.role == UserRole.MANAGER.value:
        manager_cafe_id = await get_manager_cafe_id(session, current_user.id)
    _ensure_user_can_see(booking, current_user, manager_cafe_id)

    return await _booking_to_info(session, booking)


@router.patch(
    '/{booking_id}',
    response_model=BookingInfo,
    summary='Обновление бронирования по ID',
)
async def update_booking_by_id(
    booking_id: int,
    data: BookingUpdate,
    session: Annotated[AsyncSession, Depends(get_db)],
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

    updated = await update_booking(
        session=session,
        actor_id=current_user.id,
        actor_role=current_user.role,
        actor_cafe_id=manager_cafe_id,
        booking_id=booking_id,
        **fields,
    )
    send_notification('tasks.notify_booking_updated', updated.id)

    return await _booking_to_info(session, updated)
