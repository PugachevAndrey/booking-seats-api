"""Роутер кафе."""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.deps import get_current_admin, get_current_staff, get_current_user, get_db
from schemas.cafe import CafeCreate, CafeInfo, CafeUpdate
from schemas.user import UserShortInfo
from services.cafe import (
    create_cafe,
    get_cafe,
    get_cafes,
    update_cafe,
)
from services.cafe_manager import get_manager_cafe_id
from shared.core.enums import UserRole
from shared.models.cafe import Cafe
from shared.models.cafe_manager import CafeManager
from shared.models.user import User

router = APIRouter(prefix='/cafes', tags=['Кафе'])


async def _cafe_to_info(session: AsyncSession, cafe: Cafe) -> CafeInfo:
    """Собирает CafeInfo с загруженными managers."""
    result = await session.execute(
        select(User).join(CafeManager, CafeManager.user_id == User.id).where(CafeManager.cafe_id == cafe.id),
    )
    managers = [UserShortInfo.model_validate(m) for m in result.scalars().all()]
    data = {
        field: getattr(cafe, field)
        for field in (
            'id',
            'name',
            'address',
            'phone',
            'description',
            'photo_id',
            'is_active',
            'created_at',
            'updated_at',
        )
    }
    data['managers'] = managers
    return CafeInfo(**data)


@router.get('', response_model=list[CafeInfo], summary='Список кафе')
async def list_cafes(
    session: Annotated[AsyncSession, Depends(get_db)],
    _current_user: Annotated[User, Depends(get_current_user)],
) -> list[CafeInfo]:
    """Возвращает список кафе."""
    cafes = await get_cafes(session)
    return [await _cafe_to_info(session, cafe) for cafe in cafes]


@router.post(
    '',
    response_model=CafeInfo,
    status_code=status.HTTP_201_CREATED,
    summary='Создание нового кафе',
)
async def create_cafe_endpoint(
    data: CafeCreate,
    session: Annotated[AsyncSession, Depends(get_db)],
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
    return await _cafe_to_info(session, cafe)


@router.get(
    '/{cafe_id}',
    response_model=CafeInfo,
    summary='Информация о кафе по ID',
    response_model_exclude_none=True,
)
async def get_cafe_by_id(
    cafe_id: int,
    session: Annotated[AsyncSession, Depends(get_db)],
    _current_user: Annotated[User, Depends(get_current_user)],
) -> CafeInfo:
    """Информация о кафе."""
    cafe = await get_cafe(session, cafe_id)
    return await _cafe_to_info(session, cafe)


@router.patch(
    '/{cafe_id}',
    response_model=CafeInfo,
    summary='Обновление кафе по ID',
)
async def update_cafe_by_id(
    cafe_id: int,
    data: CafeUpdate,
    session: Annotated[AsyncSession, Depends(get_db)],
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
    return await _cafe_to_info(session, cafe)
