from datetime import time
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.slot import Slot
from validators import (
    validate_slot_description,
    validate_slot_time_range,
)

from .access import ensure_cafe_access
from core.errors import NotFoundError, ValidationError

SLOT_EDITABLE_FIELDS = frozenset(
    {'start_time', 'end_time', 'description'},
)
SLOT_TIME_FIELDS = frozenset({'start_time', 'end_time'})


async def get_slot(session: AsyncSession, slot_id: int) -> Slot:
    """Возвращает активный слот по ID."""
    slot = await session.get(Slot, slot_id)
    if slot is None or not slot.is_active:
        raise NotFoundError(f'Слот {slot_id} не найден.')
    return slot


async def get_slots(
    session: AsyncSession,
    cafe_id: int | None = None,
) -> list[Slot]:
    """Возвращает список активных слотов."""
    query = select(Slot).where(Slot.is_active.is_(True))
    if cafe_id is not None:
        query = query.where(Slot.cafe_id == cafe_id)
    result = await session.execute(query.order_by(Slot.start_time))
    return list(result.scalars().all())


async def create_slot(
    session: AsyncSession,
    actor_role: str,
    actor_cafe_id: int | None,
    cafe_id: int,
    start_time: time,
    end_time: time,
    description: str | None = None,
) -> Slot:
    """Создаёт новый слот."""
    ensure_cafe_access(actor_role, actor_cafe_id, cafe_id)
    validate_slot_time_range(start_time, end_time)
    validate_slot_description(description)

    slot = Slot(
        cafe_id=cafe_id,
        start_time=start_time,
        end_time=end_time,
        description=description,
    )
    session.add(slot)
    await session.flush()
    await session.refresh(slot)
    return slot


async def update_slot(
    session: AsyncSession,
    actor_role: str,
    actor_cafe_id: int | None,
    slot_id: int,
    **fields: Any,
) -> Slot:
    """Обновляет поля слота. Перенос в другое кафе запрещён."""
    slot = await get_slot(session, slot_id)
    ensure_cafe_access(actor_role, actor_cafe_id, slot.cafe_id)

    unknown = set(fields) - SLOT_EDITABLE_FIELDS
    if unknown:
        raise ValidationError(
            f'Поля нельзя изменить: {", ".join(sorted(unknown))}.',
        )

    changes = dict(fields)

    if 'description' in changes:
        validate_slot_description(changes['description'])

    if SLOT_TIME_FIELDS & changes.keys():
        validate_slot_time_range(
            changes.get('start_time', slot.start_time),
            changes.get('end_time', slot.end_time),
        )

    for field_name, value in changes.items():
        setattr(slot, field_name, value)

    await session.flush()
    await session.refresh(slot)
    return slot


async def delete_slot(
    session: AsyncSession,
    actor_role: str,
    actor_cafe_id: int | None,
    slot_id: int,
) -> None:
    """Мягко удаляет слот."""
    slot = await get_slot(session, slot_id)
    ensure_cafe_access(actor_role, actor_cafe_id, slot.cafe_id)
    slot.is_active = False
    await session.flush()
