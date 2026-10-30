"""Роутер кафе."""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from api.v1.deps import DbSession, get_current_admin, get_current_staff, get_current_user
from schemas.cafe import CafeCreate, CafeInfo, CafeUpdate
from services.cafe import (
    create_cafe,
    get_cafe,
    get_cafes,
    update_cafe,
)
from services.cafe_manager import get_manager_cafe_id
from shared.core.enums import UserRole
from shared.models.cafe import Cafe
from shared.models.user import User

router = APIRouter(prefix='/cafes', tags=['Кафе'])


def _cafe_to_info(cafe: Cafe) -> CafeInfo:
    """Собирает CafeInfo; managers подгружаются через relationship."""
    return CafeInfo.model_validate(cafe, from_attributes=True)


@router.get('', response_model=list[CafeInfo], summary='Список кафе')
async def list_cafes(
    session: DbSession,
    current_user: Annotated[User, Depends(get_current_user)],
    show_active: bool | None = None,
) -> list[CafeInfo]:
    """Возвращает список кафе."""
    if current_user.role == UserRole.USER.value:
        is_active = True
    elif current_user.role == UserRole.MANAGER.value:
        is_active = True if show_active is None else show_active
    else:
        is_active = show_active

    cafes = await get_cafes(session, is_active=is_active)
    return [_cafe_to_info(cafe) for cafe in cafes]


@router.post(
    '',
    response_model=CafeInfo,
    status_code=status.HTTP_201_CREATED,
    summary='Создание нового кафе',
)
async def create_cafe_endpoint(
    data: CafeCreate,
    session: DbSession,
    current_user: Annotated[User, Depends(get_current_admin)],
) -> CafeInfo:
    """Создание кафе."""
    payload = data.model_dump(exclude_unset=True)
    cafe = await create_cafe(
        session=session,
        actor_role=current_user.role,
        name=payload['name'],
        address=payload['address'],
        phone=payload['phone'],
        description=payload.get('description'),
        photo_id=payload.get('photo_id'),
        managers_id=payload.get('managers_id'),
    )
    return _cafe_to_info(cafe)


@router.get(
    '/{cafe_id}',
    response_model=CafeInfo,
    summary='Информация о кафе по ID',
    response_model_exclude_none=True,
)
async def get_cafe_by_id(
    cafe_id: int,
    session: DbSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> CafeInfo:
    """Информация о кафе."""
    include_inactive = current_user.role != UserRole.USER.value
    cafe = await get_cafe(session, cafe_id, include_inactive=include_inactive)
    return _cafe_to_info(cafe)


@router.patch(
    '/{cafe_id}',
    response_model=CafeInfo,
    summary='Обновление кафе по ID',
)
async def update_cafe_by_id(
    cafe_id: int,
    data: CafeUpdate,
    session: DbSession,
    current_user: Annotated[User, Depends(get_current_staff)],
) -> CafeInfo:
    """Обновление информации о кафе."""
    actor_cafe_id = None
    if current_user.role != UserRole.ADMIN.value:
        actor_cafe_id = await get_manager_cafe_id(session, current_user.id)

    fields = data.model_dump(exclude_unset=True)
    cafe = await update_cafe(
        session=session,
        actor_role=current_user.role,
        actor_cafe_id=actor_cafe_id,
        cafe_id=cafe_id,
        **fields,
    )
    return _cafe_to_info(cafe)
