"""Роутер временных слотов кафе."""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from api.v1.deps import DbSession, get_current_staff, get_current_user
from schemas.slot import TimeSlotCreate, TimeSlotInfo, TimeSlotUpdate
from services.cafe_manager import get_manager_cafe_id
from services.slot import (
    create_slot,
    get_slot,
    get_slots,
    update_slot,
)
from shared.core.enums import UserRole
from shared.core.errors import NotFoundError
from shared.models.slot import Slot
from shared.models.user import User

router = APIRouter(
    prefix='/cafes/{cafe_id}/time_slots',
    tags=['Временные слоты'],
)


def _slot_to_info(slot: Slot) -> TimeSlotInfo:
    """Собирает TimeSlotInfo; вложенное кафе подгружается через relationship."""
    return TimeSlotInfo.model_validate(slot, from_attributes=True)


@router.get(
    '',
    response_model=list[TimeSlotInfo],
    summary='Список временных слотов в кафе',
)
async def list_slots(
    cafe_id: int,
    session: DbSession,
    current_user: Annotated[User, Depends(get_current_user)],
    show_active: bool | None = None,
) -> list[TimeSlotInfo]:
    """Возвращает список слотов."""
    if current_user.role == UserRole.USER.value:
        is_active = True
    elif current_user.role == UserRole.MANAGER.value:
        is_active = True if show_active is None else show_active
    else:
        is_active = show_active

    slots = await get_slots(session, cafe_id, is_active=is_active)
    return [_slot_to_info(s) for s in slots]


@router.post(
    '',
    response_model=TimeSlotInfo,
    status_code=status.HTTP_201_CREATED,
    summary='Новый временной слот в кафе',
)
async def create_slot_endpoint(
    cafe_id: int,
    data: TimeSlotCreate,
    session: DbSession,
    current_user: Annotated[User, Depends(get_current_staff)],
) -> TimeSlotInfo:
    """Создание слота."""
    actor_cafe_id = None
    if current_user.role != UserRole.ADMIN.value:
        actor_cafe_id = await get_manager_cafe_id(session, current_user.id)

    payload = data.model_dump(exclude_unset=True)
    slot = await create_slot(
        session=session,
        actor_role=current_user.role,
        actor_cafe_id=actor_cafe_id,
        cafe_id=cafe_id,
        start_time=payload['start_time'],
        end_time=payload['end_time'],
        description=payload.get('description'),
    )
    return _slot_to_info(slot)


@router.get(
    '/{slot_id}',
    response_model=TimeSlotInfo,
    summary='Информация о слоте по ID',
)
async def get_slot_by_id(
    cafe_id: int,
    slot_id: int,
    session: DbSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> TimeSlotInfo:
    """Информация о слоте."""
    include_inactive = current_user.role != UserRole.USER.value
    slot = await get_slot(session, slot_id, include_inactive=include_inactive)
    if slot.cafe_id != cafe_id:
        raise NotFoundError(f'Слот {slot_id} не найден в кафе {cafe_id}.')
    return _slot_to_info(slot)


@router.patch(
    '/{slot_id}',
    response_model=TimeSlotInfo,
    summary='Обновление слота по ID',
)
async def update_slot_by_id(
    cafe_id: int,
    slot_id: int,
    data: TimeSlotUpdate,
    session: DbSession,
    current_user: Annotated[User, Depends(get_current_staff)],
) -> TimeSlotInfo:
    """Обновление информации о слоте."""
    slot = await get_slot(session, slot_id, include_inactive=True)
    if slot.cafe_id != cafe_id:
        raise NotFoundError(f'Слот {slot_id} не найден в кафе {cafe_id}.')

    actor_cafe_id = None
    if current_user.role != UserRole.ADMIN.value:
        actor_cafe_id = await get_manager_cafe_id(session, current_user.id)

    fields = data.model_dump(exclude_unset=True)
    updated = await update_slot(
        session=session,
        actor_role=current_user.role,
        actor_cafe_id=actor_cafe_id,
        slot_id=slot_id,
        **fields,
    )
    return _slot_to_info(updated)
