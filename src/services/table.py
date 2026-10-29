"""Бизнес-логика столов."""

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from repositories.table import table_crud
from schemas.table import TableUpdate
from services.cafe import get_cafe
from shared.core.errors import NotFoundError, ValidationError
from shared.models.table import Table

from .access import ensure_cafe_access

TABLE_EDITABLE_FIELDS = frozenset({'description', 'seat_number'})
SEAT_NUMBER_MIN = 1


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


def _validate_seat_number(seat_number: int) -> None:
    """Проверяет количество мест.

    Схема оставляет значение без ограничения, поэтому проверяем здесь.
    """
    if seat_number < SEAT_NUMBER_MIN:
        raise ValidationError(
            'Количество мест должно быть положительным числом.',
        )


async def create_table(
    session: AsyncSession,
    actor_role: str,
    actor_cafe_id: int | None,
    cafe_id: int,
    description: str | None,
    seat_number: int,
) -> Table:
    """Создаёт новый стол.

    Длину описания проверяет схема TableCreate.
    """
    ensure_cafe_access(actor_role, actor_cafe_id, cafe_id)
    await get_cafe(session, cafe_id)
    _validate_seat_number(seat_number)

    data: dict[str, Any] = {
        'cafe_id': cafe_id,
        'seat_number': seat_number,
    }
    if description is not None:
        data['description'] = description

    table = await table_crud.create_from_dict(session=session, data=data)
    await session.commit()
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

    if 'seat_number' in changes:
        _validate_seat_number(changes['seat_number'])

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
