from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.table import Table
from validators import (
    validate_table_description,
    validate_table_seat_number,
)

from .access import ensure_cafe_access
from core.errors import NotFoundError, ValidationError

TABLE_EDITABLE_FIELDS = frozenset({'description', 'seat_number'})


async def get_table(session: AsyncSession, table_id: int) -> Table:
    """Возвращает активный стол по ID."""
    table = await session.get(Table, table_id)
    if table is None or not table.is_active:
        raise NotFoundError(f'Стол {table_id} не найден.')
    return table


async def get_tables(
    session: AsyncSession,
    cafe_id: int | None = None,
) -> list[Table]:
    """Возвращает список активных столов."""
    query = select(Table).where(Table.is_active.is_(True))
    if cafe_id is not None:
        query = query.where(Table.cafe_id == cafe_id)
    result = await session.execute(query.order_by(Table.id))
    return list(result.scalars().all())


async def create_table(
    session: AsyncSession,
    actor_role: str,
    actor_cafe_id: int | None,
    cafe_id: int,
    description: str | None,
    seat_number: int,
) -> Table:
    """Создаёт новый стол."""
    ensure_cafe_access(actor_role, actor_cafe_id, cafe_id)
    validate_table_seat_number(seat_number)
    validate_table_description(description)

    table = Table(
        cafe_id=cafe_id,
        description=description,
        seat_number=seat_number,
    )
    session.add(table)
    await session.flush()
    await session.refresh(table)
    return table


async def update_table(
    session: AsyncSession,
    actor_role: str,
    actor_cafe_id: int | None,
    table_id: int,
    **fields: Any,
) -> Table:
    """Обновляет поля стола. Перенос в другое кафе запрещён."""
    table = await get_table(session, table_id)
    ensure_cafe_access(actor_role, actor_cafe_id, table.cafe_id)

    unknown = set(fields) - TABLE_EDITABLE_FIELDS
    if unknown:
        raise ValidationError(
            f'Поля нельзя изменить: {", ".join(sorted(unknown))}.',
        )

    changes = dict(fields)
    if 'description' in changes:
        validate_table_description(changes['description'])
    if 'seat_number' in changes:
        validate_table_seat_number(changes['seat_number'])

    for field_name, value in changes.items():
        setattr(table, field_name, value)

    await session.flush()
    await session.refresh(table)
    return table


async def delete_table(
    session: AsyncSession,
    actor_role: str,
    actor_cafe_id: int | None,
    table_id: int,
) -> None:
    """Мягко удаляет стол."""
    table = await get_table(session, table_id)
    ensure_cafe_access(actor_role, actor_cafe_id, table.cafe_id)
    table.is_active = False
    await session.flush()
