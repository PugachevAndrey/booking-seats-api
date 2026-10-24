from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.deps import get_current_user, get_db
from schemas.booking import BookingCreate, BookingInfo, BookingUpdate
from services.booking import (
    create_booking,
    get_booking,
    get_bookings,
    update_booking,
)
from services.cafe_manager import get_manager_cafe_id
from shared.celery_client import celery_client
from shared.core.enums import BookingStatus, UserRole
from shared.core.errors import PermissionDeniedError, ValidationError
from shared.models.booking import Booking
from shared.models.user import User

router = APIRouter(prefix='/booking', tags=['Бронирования'])


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
) -> list[Booking]:
    """Возвращает список бронирований."""
    actor_cafe_id = None
    if current_user.role == UserRole.MANAGER.value:
        actor_cafe_id = await get_manager_cafe_id(session, current_user.id)

    return await get_bookings(
        session,
        actor_id=current_user.id,
        actor_role=current_user.role,
        actor_cafe_id=actor_cafe_id,
    )


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
) -> Booking:
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
    celery_client.send_task(
        'tasks.notify_booking_created',
        args=[booking.id],
    )
    return booking


@router.get(
    '/{booking_id}',
    response_model=BookingInfo,
    summary='Информация о бронировании по ID',
)
async def get_booking_by_id(
    booking_id: int,
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Booking:
    """Информация о бронировании."""
    booking = await get_booking(session, booking_id)

    manager_cafe_id = None
    if current_user.role == UserRole.MANAGER.value:
        manager_cafe_id = await get_manager_cafe_id(session, current_user.id)
    _ensure_user_can_see(booking, current_user, manager_cafe_id)

    return booking


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
) -> Booking:
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

    booking = await update_booking(
        session=session,
        actor_id=current_user.id,
        actor_role=current_user.role,
        actor_cafe_id=manager_cafe_id,
        booking_id=booking_id,
        **fields,
    )
    celery_client.send_task(
        'tasks.notify_booking_updated',
        args=[booking.id],
    )
    return booking
