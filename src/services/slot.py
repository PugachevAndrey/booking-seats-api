from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.slot import Slot

from .access import ensure_cafe_access
from .errors import NotFoundError, ValidationError


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
    start_time: datetime,
    end_time: datetime,
    description: str,
) -> Slot:
    """Создаёт новый слот."""
    ensure_cafe_access(actor_role, actor_cafe_id, cafe_id)
    if end_time <= start_time:
        raise ValidationError('Время завершения должно быть позже времени начала.')

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
    **fields: object,
) -> Slot:
    """Обновляет поля слота с проверкой прав."""
    slot = await get_slot(session, slot_id)
    ensure_cafe_access(actor_role, actor_cafe_id, slot.cafe_id)
    allowed = {'cafe_id', 'start_time', 'end_time', 'description'}
    for name, value in fields.items():
        if name in allowed:
            setattr(slot, name, value)
    if slot.end_time <= slot.start_time:
        raise ValidationError('Время завершения должно быть позже времени начала.')
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
