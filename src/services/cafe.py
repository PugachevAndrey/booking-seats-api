"""Бизнес-логика кафе."""

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from repositories.cafe import cafe_crud
from schemas.cafe import CafeUpdate
from shared.core.errors import NotFoundError, ValidationError
from shared.models.cafe import Cafe

from .access import ensure_admin, ensure_cafe_access
from .cafe_manager import (
    delete_cafe_managers,
    sync_cafe_managers,
)

CAFE_EDITABLE_FIELDS = frozenset(
    {'name', 'address', 'phone', 'description', 'photo_id'},
)


async def get_cafe(
    session: AsyncSession,
    cafe_id: int,
    include_inactive: bool = False,
) -> Cafe:
    """Возвращает кафе по ID.

    include_inactive=True — для персонала: мягко удалённые кафе видны.
    """
    cafe = await cafe_crud.get(session=session, obj_id=cafe_id)
    if cafe is None:
        raise NotFoundError(f'Кафе {cafe_id} не найдено.')
    if not cafe.is_active and not include_inactive:
        raise NotFoundError(f'Кафе {cafe_id} не найдено.')
    return cafe


async def get_cafes(
    session: AsyncSession,
    include_inactive: bool = False,
) -> list[Cafe]:
    """Возвращает список кафе.

    include_inactive=True — для персонала, видны мягко удалённые кафе.
    """
    cafes = await cafe_crud.get_multi(session=session)
    if not include_inactive:
        cafes = [cafe for cafe in cafes if cafe.is_active]
    return sorted(cafes, key=lambda cafe: cafe.id)


async def create_cafe(
    session: AsyncSession,
    actor_role: str,
    name: str,
    address: str,
    phone: str,
    description: str | None,
    photo_id: uuid.UUID,
    managers_id: list[int] | None = None,
) -> Cafe:
    """Создаёт кафе и привязывает менеджеров.

    Длины и формат полей проверяет схема CafeCreate.
    """
    ensure_admin(actor_role)

    cafe = await cafe_crud.create_from_dict(
        session=session,
        data={
            'name': name,
            'address': address,
            'phone': phone,
            'description': description,
            'photo_id': photo_id,
        },
    )

    await sync_cafe_managers(session, cafe.id, managers_id or None)

    return cafe


async def update_cafe(
    session: AsyncSession,
    actor_role: str,
    actor_cafe_id: int | None,
    cafe_id: int,
    **fields: Any,
) -> Cafe:
    """Обновляет поля кафе. Менеджеров меняет только админ.

    Править мягко удалённое кафе персоналу можно — поэтому
    include_inactive=True.
    """
    cafe = await get_cafe(session, cafe_id, include_inactive=True)

    managers_requested = 'managers_id' in fields
    managers_id = fields.pop('managers_id', None)

    if managers_requested:
        ensure_admin(actor_role)
    else:
        ensure_cafe_access(actor_role, actor_cafe_id, cafe_id)

    unknown = set(fields) - CAFE_EDITABLE_FIELDS
    if unknown:
        raise ValidationError(
            f'Поля нельзя изменить: {", ".join(sorted(unknown))}.',
        )

    changes = dict(fields)

    if managers_requested:
        await sync_cafe_managers(session, cafe_id, managers_id)

    if changes:
        cafe = await cafe_crud.update(
            session=session,
            db_obj=cafe,
            obj_in=CafeUpdate(**changes),
        )

    return cafe


async def delete_cafe(
    session: AsyncSession,
    actor_role: str,
    cafe_id: int,
) -> None:
    """Мягко удаляет кафе и отвязывает менеджеров."""
    ensure_admin(actor_role)
    cafe = await get_cafe(session, cafe_id, include_inactive=True)

    await delete_cafe_managers(session, actor_role, cafe_id)

    await cafe_crud.update(
        session=session,
        db_obj=cafe,
        obj_in=CafeUpdate(is_active=False),
    )
