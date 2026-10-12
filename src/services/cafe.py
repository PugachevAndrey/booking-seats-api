"""Сервисные функции для работы с кафе."""

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.cafe import Cafe

from .access import ensure_admin, ensure_cafe_access, ensure_staff
from .errors import ConflictError, NotFoundError


async def get_cafe(session: AsyncSession, cafe_id: int) -> Cafe:
    """Возвращает активное кафе по ID."""
    cafe = await session.get(Cafe, cafe_id)
    if cafe is None or not cafe.is_active:
        raise NotFoundError(f'Кафе {cafe_id} не найдено.')
    return cafe


async def get_cafes(session: AsyncSession) -> list[Cafe]:
    """Возвращает список активных кафе."""
    result = await session.execute(
        select(Cafe).where(Cafe.is_active.is_(True)).order_by(Cafe.id)
    )
    return list(result.scalars().all())


async def _ensure_photo_free(
    session: AsyncSession,
    photo_id: uuid.UUID,
    exclude_cafe_id: int | None = None,
) -> None:
    """Проверяет, что фото не привязано к другому кафе."""
    query = select(Cafe).where(Cafe.photo_id == photo_id)
    if exclude_cafe_id is not None:
        query = query.where(Cafe.id != exclude_cafe_id)
    result = await session.execute(query)
    if result.first() is not None:
        raise ConflictError('Это фото уже используется другим кафе.')


async def create_cafe(
    session: AsyncSession,
    actor_role: str,
    name: str,
    address: str,
    phone: str,
    description: str,
    photo_id: uuid.UUID,
) -> Cafe:
    """Создаёт новое кафе."""
    ensure_staff(actor_role)
    await _ensure_photo_free(session, photo_id)

    cafe = Cafe(
        name=name,
        address=address,
        phone=phone,
        description=description,
        photo_id=photo_id,
    )
    session.add(cafe)
    await session.flush()
    await session.refresh(cafe)
    return cafe


async def update_cafe(
    session: AsyncSession,
    actor_role: str,
    actor_cafe_id: int | None,
    cafe_id: int,
    **fields: Any,
) -> Cafe:
    """Обновляет поля кафе с проверкой прав."""
    ensure_cafe_access(actor_role, actor_cafe_id, cafe_id)
    cafe = await get_cafe(session, cafe_id)
    if 'photo_id' in fields:
        await _ensure_photo_free(
            session,
            fields['photo_id'],
            exclude_cafe_id=cafe_id,
        )
    allowed = {'name', 'address', 'phone', 'description', 'photo_id'}
    for name, value in fields.items():
        if name in allowed:
            setattr(cafe, name, value)
    await session.flush()
    await session.refresh(cafe)
    return cafe


async def delete_cafe(
    session: AsyncSession,
    actor_role: str,
    actor_cafe_id: int | None,
    cafe_id: int,
) -> None:
    """Мягко удаляет кафе."""
    ensure_admin(actor_role)
    cafe = await get_cafe(session, cafe_id)
    cafe.is_active = False
    await session.flush()
