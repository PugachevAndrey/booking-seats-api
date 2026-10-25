"""Роутер временных слотов кафе."""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.deps import get_current_staff, get_current_user, get_db
from schemas.cafe import CafeShortInfo
from schemas.slot import TimeSlotCreate, TimeSlotInfo, TimeSlotUpdate
from services.cafe import get_cafe
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


async def _slot_to_info(session: AsyncSession, slot: Slot) -> TimeSlotInfo:
    """Собирает TimeSlotInfo с вложенным кафе (без relationship в модели)."""
    cafe = await get_cafe(session, slot.cafe_id)
    return TimeSlotInfo(
        id=slot.id,
        cafe=CafeShortInfo.model_validate(cafe, from_attributes=True),
        start_time=slot.start_time,
        end_time=slot.end_time,
        description=slot.description,
        is_active=slot.is_active,
        created_at=slot.created_at,
        updated_at=slot.updated_at,
    )


@router.get(
    '',
    response_model=list[TimeSlotInfo],
    summary='Список временных слотов в кафе',
)
async def list_slots(
    cafe_id: int,
    session: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> list[TimeSlotInfo]:
    """Возвращает список слотов."""
    slots = await get_slots(session, cafe_id)
    return [await _slot_to_info(session, s) for s in slots]


@router.post(
    '',
    response_model=TimeSlotInfo,
    status_code=status.HTTP_201_CREATED,
    summary='Новый временной слот в кафе',
)
async def create_slot_endpoint(
    cafe_id: int,
    data: TimeSlotCreate,
    session: Annotated[AsyncSession, Depends(get_db)],
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
    return await _slot_to_info(session, slot)


@router.get(
    '/{slot_id}',
    response_model=TimeSlotInfo,
    summary='Информация о слоте по ID',
)
async def get_slot_by_id(
    cafe_id: int,
    slot_id: int,
    session: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> TimeSlotInfo:
    """Информация о слоте."""
    slot = await get_slot(session, slot_id)
    if slot.cafe_id != cafe_id:
        raise NotFoundError(f'Слот {slot_id} не найден в кафе {cafe_id}.')
    return await _slot_to_info(session, slot)


@router.patch(
    '/{slot_id}',
    response_model=TimeSlotInfo,
    summary='Обновление слота по ID',
)
async def update_slot_by_id(
    cafe_id: int,
    slot_id: int,
    data: TimeSlotUpdate,
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_staff)],
) -> TimeSlotInfo:
    """Обновление информации о слоте."""
    slot = await get_slot(session, slot_id)
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
    return await _slot_to_info(session, updated)
