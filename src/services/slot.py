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


async def _ensure_no_time_overlap(
    session: AsyncSession,
    cafe_id: int,
    start_time: time,
    end_time: time,
    exclude_slot_id: int | None = None,
) -> None:
    """Проверяет пересечение с другими активными слотами кафе через SQL."""
    overlap = await slot_crud.check_overlap(
        session=session,
        cafe_id=cafe_id,
        start_time=start_time,
        end_time=end_time,
        exclude_slot_id=exclude_slot_id,
    )
    if overlap:
        raise ValidationError(
            'Временной слот пересекается с другим активным слотом кафе.',
        )


async def get_slot(
    session: AsyncSession,
    slot_id: int,
    *,
    include_inactive: bool = False,
) -> Slot:
    """Возвращает слот по ID; по умолчанию только активный."""
    slot = await slot_crud.get(session=session, obj_id=slot_id)
    if slot is None or (not include_inactive and not slot.is_active):
        raise NotFoundError(f'Слот {slot_id} не найден.')
    return slot


async def get_slots(
    session: AsyncSession,
    cafe_id: int | None = None,
    is_active: bool | None = True,
    skip: int = 0,
    limit: int = 100,
) -> list[Slot]:
    """Возвращает слоты: None — все, True — активные, False — неактивные."""
    if cafe_id is None:
        return await slot_crud.get_multi(
            session=session,
            skip=skip,
            limit=limit,
            is_active=is_active if is_active is not None else None,
        )

    return await slot_crud.get_by_cafe(
        session=session,
        cafe_id=cafe_id,
        is_active=is_active,
        skip=skip,
        limit=limit,
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

    await _ensure_no_time_overlap(
        session=session,
        cafe_id=cafe_id,
        start_time=start_time,
        end_time=end_time,
    )

    data: dict[str, Any] = {
        'cafe_id': cafe_id,
        'start_time': start_time,
        'end_time': end_time,
    }
    if description is not None:
        data['description'] = description

    slot = await slot_crud.create_from_dict(session=session, data=data)
    await session.flush()
    return slot


async def update_slot(
    session: AsyncSession,
    actor_role: str,
    actor_cafe_id: int | None,
    slot_id: int,
    **fields: Any,
) -> Slot:
    """Обновляет поля слота. Перенос в другое кафе запрещён."""
    slot = await get_slot(session, slot_id, include_inactive=True)
    ensure_cafe_access(actor_role, actor_cafe_id, slot.cafe_id)

    unknown = set(fields) - SLOT_EDITABLE_FIELDS
    if unknown:
        raise ValidationError(
            f'Поля нельзя изменить: {", ".join(sorted(unknown))}.',
        )

    changes = dict(fields)

    start_time = changes.get('start_time', slot.start_time)
    end_time = changes.get('end_time', slot.end_time)
    will_be_active = changes.get('is_active', slot.is_active)

    if SLOT_TIME_FIELDS & changes.keys() or will_be_active:
        validate_slot_time_range(start_time, end_time)

    if will_be_active:
        await _ensure_no_time_overlap(
            session=session,
            cafe_id=slot.cafe_id,
            start_time=start_time,
            end_time=end_time,
            exclude_slot_id=slot.id,
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
