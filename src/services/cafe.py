import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.cafe import Cafe

from .access import ensure_admin, ensure_cafe_access
from .cafe_manager import (
    delete_cafe_managers,
    sync_cafe_managers,
)
from .errors import ConflictError, NotFoundError, ValidationError
from .validations import (
    validate_cafe_description,
    validate_cafe_fields,
)

CAFE_EDITABLE_FIELDS = frozenset(
    {'name', 'address', 'phone', 'description', 'photo_id'},
)


async def get_cafe(session: AsyncSession, cafe_id: int) -> Cafe:
    """Возвращает активное кафе по ID."""
    cafe = await session.get(Cafe, cafe_id)
    if cafe is None or not cafe.is_active:
        raise NotFoundError(f'Кафе {cafe_id} не найдено.')
    return cafe


async def get_cafes(session: AsyncSession) -> list[Cafe]:
    """Возвращает список активных кафе."""
    result = await session.execute(
        select(Cafe).where(Cafe.is_active.is_(True)).order_by(Cafe.id),
    )
    return list(result.scalars().all())


async def _ensure_photo_free(
    session: AsyncSession,
    photo_id: uuid.UUID,
    exclude_cafe_id: int | None = None,
) -> None:
    """Проверяет, что фото не привязано к другому кафе."""
    query = select(Cafe).where(
        Cafe.photo_id == photo_id,
        Cafe.is_active.is_(True),
    )
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

    cafe = Cafe(
        name=name,
        address=address,
        phone=phone,
        description=description,
        photo_id=photo_id,
    )
    session.add(cafe)
    await session.flush()

    await sync_cafe_managers(session, cafe.id, managers_id)

    await session.refresh(cafe)
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

    if 'photo_id' in changes:
        photo_id = changes['photo_id']
        if photo_id is not None:
            await _ensure_photo_free(
                session,
                photo_id,
                exclude_cafe_id=cafe_id,
            )

    await sync_cafe_managers(session, cafe_id, managers_id)

    for field_name, value in changes.items():
        setattr(cafe, field_name, value)

    await session.flush()
    await session.refresh(cafe)
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
    cafe.photo_id = None
    cafe.is_active = False
    await session.flush()
