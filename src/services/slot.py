"""Бизнес-логика временных слотов."""

from datetime import time
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from repositories.slot import slot_crud
from schemas.slot import TimeSlotUpdate
from services.cafe import get_cafe
from shared.core.errors import NotFoundError, ValidationError
from shared.models.slot import Slot
from validators import validate_slot_time_range

from .access import ensure_cafe_access

SLOT_EDITABLE_FIELDS = frozenset(
    {'start_time', 'end_time', 'description', 'is_active'},
)
SLOT_TIME_FIELDS = frozenset({'start_time', 'end_time'})


async def get_slot(session: AsyncSession, slot_id: int) -> Slot:
    """Возвращает активный слот по ID."""
    slot = await slot_crud.get(session=session, obj_id=slot_id)
    if slot is None or not slot.is_active:
        raise NotFoundError(f'Слот {slot_id} не найден.')
    return slot


async def get_slots(
    session: AsyncSession,
    cafe_id: int | None = None,
) -> list[Slot]:
    """Возвращает список активных слотов."""
    if cafe_id is None:
        slots = await slot_crud.get_multi(session=session)
    else:
        slots = await slot_crud.get_by_cafe(session=session, cafe_id=cafe_id)

    return sorted(
        (slot for slot in slots if slot.is_active),
        key=lambda slot: slot.start_time,
    )


async def create_slot(
    session: AsyncSession,
    actor_role: str,
    actor_cafe_id: int | None,
    cafe_id: int,
    start_time: time,
    end_time: time,
    description: str | None = None,
) -> Slot:
    """Создаёт новый слот.

    Длину описания проверяет схема TimeSlotCreate.
    """
    ensure_cafe_access(actor_role, actor_cafe_id, cafe_id)
    await get_cafe(session, cafe_id)
    validate_slot_time_range(start_time, end_time)

    data: dict[str, Any] = {
        'cafe_id': cafe_id,
        'start_time': start_time,
        'end_time': end_time,
    }
    if description is not None:
        data['description'] = description

    slot = await slot_crud.create_from_dict(session=session, data=data)
    await session.commit()
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

    if SLOT_TIME_FIELDS & changes.keys():
        validate_slot_time_range(
            changes.get('start_time', slot.start_time),
            changes.get('end_time', slot.end_time),
        )

    return await slot_crud.update(
        session=session,
        db_obj=slot,
        obj_in=TimeSlotUpdate(**changes),
    )


async def delete_slot(
    session: AsyncSession,
    actor_role: str,
    actor_cafe_id: int | None,
    slot_id: int,
) -> None:
    """Мягко удаляет слот."""
    slot = await get_slot(session, slot_id)
    ensure_cafe_access(actor_role, actor_cafe_id, slot.cafe_id)

    await slot_crud.update(
        session=session,
        db_obj=slot,
        obj_in=TimeSlotUpdate(is_active=False),
    )
