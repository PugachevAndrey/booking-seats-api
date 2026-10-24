import uuid
from typing import Any

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from repositories.cafe import cafe_crud
from schemas.cafe import CafeUpdate
from shared.core.errors import ConflictError, NotFoundError, ValidationError
from shared.models.cafe import Cafe
from validators import (
    validate_cafe_description,
    validate_cafe_fields,
)

from .access import ensure_admin, ensure_cafe_access
from .cafe_manager import (
    delete_cafe_managers,
    sync_cafe_managers,
)

CAFE_EDITABLE_FIELDS = frozenset(
    {'name', 'address', 'phone', 'description', 'photo_id'},
)


class _CafeCreate(BaseModel):
    """Внутренняя схема создания кафе."""

    name: str
    address: str
    phone: str
    description: str | None = None
    photo_id: uuid.UUID | None = None


async def get_cafe(session: AsyncSession, cafe_id: int) -> Cafe:
    """Возвращает активное кафе по ID."""
    cafe = await cafe_crud.get(session=session, obj_id=cafe_id)
    if cafe is None or not cafe.is_active:
        raise NotFoundError(f'Кафе {cafe_id} не найдено.')
    return cafe


async def get_cafes(session: AsyncSession) -> list[Cafe]:
    """Возвращает список активных кафе."""
    cafes = await cafe_crud.get_multi(session=session)
    return sorted(
        (cafe for cafe in cafes if cafe.is_active),
        key=lambda cafe: cafe.id,
    )


async def _ensure_photo_free(
    session: AsyncSession,
    photo_id: uuid.UUID,
    exclude_cafe_id: int | None = None,
) -> None:
    """Проверяет, что фото не привязано к другому кафе."""
    cafe = await cafe_crud.get_by_attribute(
        session=session,
        attribute='photo_id',
        value=photo_id,
    )
    if cafe is None or not cafe.is_active:
        return
    if exclude_cafe_id is not None and cafe.id == exclude_cafe_id:
        return
    raise ConflictError('Это фото уже используется другим кафе.')


async def create_cafe(
    session: AsyncSession,
    actor_role: str,
    name: str,
    address: str,
    phone: str,
    description: str | None = None,
    photo_id: uuid.UUID | None = None,
    managers_id: list[int] | None = None,
) -> Cafe:
    """Создаёт кафе и привязывает менеджеров."""
    ensure_admin(actor_role)
    validate_cafe_fields(name, address, phone)
    validate_cafe_description(description)
    if photo_id is not None:
        await _ensure_photo_free(session, photo_id)

    cafe = await cafe_crud.create(
        session=session,
        obj_in=_CafeCreate(
            name=name,
            address=address,
            phone=phone,
            description=description,
            photo_id=photo_id,
        ),
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
    """Обновляет поля кафе. Менеджеров меняет только админ."""
    cafe = await get_cafe(session, cafe_id)

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

    if {'name', 'address', 'phone'} & changes.keys():
        validate_cafe_fields(
            changes.get('name', cafe.name),
            changes.get('address', cafe.address),
            changes.get('phone', cafe.phone),
        )
    if 'description' in changes:
        validate_cafe_description(changes['description'])

    if 'photo_id' in changes and changes['photo_id'] is not None:
        await _ensure_photo_free(
            session,
            changes['photo_id'],
            exclude_cafe_id=cafe_id,
        )

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
    cafe = await get_cafe(session, cafe_id)

    await delete_cafe_managers(session, actor_role, cafe_id)

    await cafe_crud.update(
        session=session,
        db_obj=cafe,
        obj_in=CafeUpdate(is_active=False, photo_id=None),
    )
