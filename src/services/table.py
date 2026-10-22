from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from models.table import Table
from repositories.table import table_crud
from schemas.table import TableCreate, TableUpdate
from validators import (
    validate_table_description,
    validate_table_seat_number,
)

from .access import ensure_cafe_access
from core.errors import NotFoundError, ValidationError

TABLE_EDITABLE_FIELDS = frozenset({'description', 'seat_number'})


async def get_table(session: AsyncSession, table_id: int) -> Table:
    """Возвращает активный стол по ID."""
    table = await table_crud.get(session=session, obj_id=table_id)
    if table is None or not table.is_active:
        raise NotFoundError(f'Стол {table_id} не найден.')
    return table


async def get_tables(
    session: AsyncSession,
    cafe_id: int | None = None,
) -> list[Table]:
    """Возвращает список активных столов."""
    if cafe_id is None:
        tables = await table_crud.get_multi(session=session)
    else:
        tables = await table_crud.get_by_cafe(session=session, cafe_id=cafe_id)

    return sorted(
        (table for table in tables if table.is_active),
        key=lambda table: table.id,
    )


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

    payload: dict[str, Any] = {'seat_number': seat_number}
    if description is not None:
        payload['description'] = description

    obj_in = TableCreate(**payload).model_copy(update={'cafe_id': cafe_id})

    return await table_crud.create(session=session, obj_in=obj_in)


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
        if changes['description'] is None:
            raise ValidationError('Описание нельзя очистить через None.')
        validate_table_description(changes['description'])

    if 'seat_number' in changes:
        validate_table_seat_number(changes['seat_number'])

    return await table_crud.update(
        session=session,
        db_obj=table,
        obj_in=TableUpdate(**changes),
    )


async def delete_table(
    session: AsyncSession,
    actor_role: str,
    actor_cafe_id: int | None,
    table_id: int,
) -> None:
    """Мягко удаляет стол."""
    table = await get_table(session, table_id)
    ensure_cafe_access(actor_role, actor_cafe_id, table.cafe_id)

    await table_crud.update(
        session=session,
        db_obj=table,
        obj_in=TableUpdate(is_active=False),
    )
