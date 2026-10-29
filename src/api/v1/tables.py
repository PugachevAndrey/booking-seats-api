"""Роутер столов кафе."""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from api.v1.deps import DbSession, get_current_staff, get_current_user
from schemas.table import TableCreate, TableInfo, TableUpdate
from services.cafe_manager import get_manager_cafe_id
from services.table import (
    create_table,
    get_table,
    get_tables,
    update_table,
)
from shared.core.enums import UserRole
from shared.core.errors import NotFoundError
from shared.models.table import Table
from shared.models.user import User

router = APIRouter(prefix='/cafes/{cafe_id}/tables', tags=['Столы'])


def _table_to_info(table: Table) -> TableInfo:
    """Собирает TableInfo; вложенное кафе подгружается через relationship."""
    return TableInfo.model_validate(table, from_attributes=True)


@router.get('', response_model=list[TableInfo], summary='Список столов в кафе')
async def list_tables(
    cafe_id: int,
    session: DbSession,
    _: Annotated[User, Depends(get_current_user)],
) -> list[TableInfo]:
    """Возвращает список столиков."""
    tables = await get_tables(session, cafe_id)
    return [_table_to_info(t) for t in tables]


@router.post(
    '',
    response_model=TableInfo,
    status_code=status.HTTP_201_CREATED,
    summary='Новый стол в кафе',
)
async def create_table_endpoint(
    cafe_id: int,
    data: TableCreate,
    session: DbSession,
    current_user: Annotated[User, Depends(get_current_staff)],
) -> TableInfo:
    """Создание столика."""
    actor_cafe_id = None
    if current_user.role != UserRole.ADMIN.value:
        actor_cafe_id = await get_manager_cafe_id(session, current_user.id)

    payload = data.model_dump(exclude_unset=True)
    table = await create_table(
        session=session,
        actor_role=current_user.role,
        actor_cafe_id=actor_cafe_id,
        cafe_id=cafe_id,
        description=payload.get('description'),
        seat_number=payload['seat_number'],
    )
    return _table_to_info(table)


@router.get(
    '/{table_id}',
    response_model=TableInfo,
    summary='Информация о столе по ID',
)
async def get_table_by_id(
    cafe_id: int,
    table_id: int,
    session: DbSession,
    _: Annotated[User, Depends(get_current_user)],
) -> TableInfo:
    """Возвращает столик."""
    table = await get_table(session, table_id)
    if table.cafe_id != cafe_id:
        raise NotFoundError(f'Стол {table_id} не найден в кафе {cafe_id}.')
    return _table_to_info(table)


@router.patch(
    '/{table_id}',
    response_model=TableInfo,
    summary='Обновление стола по ID',
)
async def update_table_by_id(
    cafe_id: int,
    table_id: int,
    data: TableUpdate,
    session: DbSession,
    current_user: Annotated[User, Depends(get_current_staff)],
) -> TableInfo:
    """Обновление информации о столике."""
    table = await get_table(session, table_id)
    if table.cafe_id != cafe_id:
        raise NotFoundError(f'Стол {table_id} не найден в кафе {cafe_id}.')

    actor_cafe_id = None
    if current_user.role != UserRole.ADMIN.value:
        actor_cafe_id = await get_manager_cafe_id(session, current_user.id)

    fields = data.model_dump(exclude_unset=True)
    updated = await update_table(
        session=session,
        actor_role=current_user.role,
        actor_cafe_id=actor_cafe_id,
        table_id=table_id,
        **fields,
    )
    return _table_to_info(updated)
