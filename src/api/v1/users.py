from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.deps import (
    get_current_staff,
    get_current_user,
    get_db,
    get_optional_user,
)
from models.user import User
from schemas.user import UserCreate, UserInfo, UserUpdate
from services.cafe_manager import get_manager_cafe_id
from services.user import (
    create_user,
    get_user,
    get_users,
    update_user,
)

from core.errors import NotFoundError, PermissionDeniedError

router = APIRouter(prefix='/users', tags=['Пользователи'])


def _prepare_update_fields(
    data: UserUpdate,
    allow_admin_fields: bool,
) -> dict:
    """Отбирает переданные поля из UserUpdate."""
    raw = data.model_dump(exclude_unset=True)
    fields: dict = {}

    for key in ('username', 'email', 'phone', 'tg_id'):
        if key in raw and raw[key] is not None:
            fields[key] = raw[key]

    if 'password' in raw and raw['password'] is not None:
        fields['password_hash'] = User.hash_password(raw['password'])

    if allow_admin_fields:
        if 'role' in raw and raw['role'] is not None:
            role_value = raw['role']
            fields['role'] = getattr(role_value, 'value', role_value)
        if 'is_active' in raw and raw['is_active'] is not None:
            fields['is_active'] = raw['is_active']

    return fields


async def _ensure_manager_sees_user(
    session: AsyncSession,
    current_user: User,
    user_id: int,
) -> None:
    """Менеджер может видеть только пользователей своего кафе."""
    if current_user.role == 'admin':
        return
    cafe_id = await get_manager_cafe_id(session, current_user.id)
    if cafe_id is None:
        raise PermissionDeniedError('Менеджер не привязан к кафе.')
    visible = await get_users(session, current_user.role, cafe_id)
    if all(user.id != user_id for user in visible):
        raise NotFoundError(f'Пользователь {user_id} не найден.')


@router.get(
    '',
    response_model=list[UserInfo],
    summary='Получение списка пользователей',
)
async def list_users(
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_staff)],
) -> list[User]:
    """Список пользователей. Только админ или менеджер."""
    cafe_id = None
    if current_user.role != 'admin':
        cafe_id = await get_manager_cafe_id(session, current_user.id)
    return await get_users(session, current_user.role, cafe_id)


@router.post(
    '',
    response_model=UserInfo,
    status_code=status.HTTP_201_CREATED,
    summary='Регистрация нового пользователя',
)
async def register_user(
    data: UserCreate,
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_user)],
) -> User:
    """Регистрация. Доступна анониму, менеджеру и админу."""
    if current_user is not None and current_user.role == 'user':
        raise PermissionDeniedError('Нет прав на регистрацию пользователей.')

    payload = data.model_dump(exclude_unset=True)
    return await create_user(
        session=session,
        username=payload['username'],
        email=payload.get('email'),
        phone=payload.get('phone'),
        tg_id=payload.get('tg_id'),
        password_hash=User.hash_password(data.password),
    )


@router.get(
    '/me',
    response_model=UserInfo,
    summary='Информация о текущем пользователе',
    response_model_exclude_none=True,
)
async def get_me(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Профиль текущего пользователя."""
    return current_user


@router.patch(
    '/me',
    response_model=UserInfo,
    summary='Обновление текущего пользователя',
)
async def update_me(
    data: UserUpdate,
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Обновление своего профиля. Роль и is_active менять нельзя."""
    fields = _prepare_update_fields(data, allow_admin_fields=False)
    return await update_user(
        session=session,
        actor_id=current_user.id,
        actor_role=current_user.role,
        user_id=current_user.id,
        **fields,
    )


@router.get(
    '/{user_id}',
    response_model=UserInfo,
    summary='Информация о пользователе по ID',
    response_model_exclude_none=True,
)
async def get_user_by_id(
    user_id: int,
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_staff)],
) -> User:
    """Пользователь по ID. Менеджер — только из своего кафе."""
    await _ensure_manager_sees_user(session, current_user, user_id)
    return await get_user(session, user_id)


@router.patch(
    '/{user_id}',
    response_model=UserInfo,
    summary='Обновление пользователя по ID',
)
async def update_user_by_id(
    user_id: int,
    data: UserUpdate,
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_staff)],
) -> User:
    """Обновление пользователя. Админ — любые поля, менеджер — профиль."""
    await _ensure_manager_sees_user(session, current_user, user_id)
    is_admin = current_user.role == 'admin'
    fields = _prepare_update_fields(data, allow_admin_fields=is_admin)
    return await update_user(
        session=session,
        actor_id=current_user.id,
        actor_role=current_user.role,
        user_id=user_id,
        **fields,
    )
