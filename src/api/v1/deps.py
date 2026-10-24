"""Зависимости FastAPI: доступ к БД, текущий пользователь, проверка прав."""

from collections.abc import AsyncGenerator
from typing import Annotated

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from services.access import is_admin, is_staff
from services.user import get_user
from shared.core.db import get_session
from shared.core.errors import NotFoundError, PermissionDeniedError, UnauthorizedError
from shared.core.security import decode_access_token
from shared.models.user import User

bearer_scheme = HTTPBearer(auto_error=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Обёртка над `get_session` для `Depends`."""
    async with get_session() as session:
        yield session  # noqa: ASYNC119


async def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """Возвращает текущего пользователя по JWT из заголовка Authorization."""
    if credentials is None or not credentials.credentials:
        raise PermissionDeniedError('Требуется авторизация.')

    try:
        payload = decode_access_token(credentials.credentials)
    except jwt.PyJWTError:
        raise UnauthorizedError('Недействительный токен.')

    subject = payload.get('sub')
    if subject is None:
        raise UnauthorizedError('Недействительный токен.')

    try:
        user_id = int(subject)
    except (TypeError, ValueError):
        raise UnauthorizedError('Недействительный токен.')

    try:
        return await get_user(session, user_id)
    except NotFoundError:
        raise UnauthorizedError('Недействительный токен.')


async def get_current_staff(
    user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Текущий пользователь с ролью администратора или менеджера."""
    if not is_staff(user.role):
        raise PermissionDeniedError(
            'Требуется роль администратора или менеджера.',
        )
    return user


async def get_current_admin(
    user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Текущий пользователь с ролью администратора."""
    if not is_admin(user.role):
        raise PermissionDeniedError('Требуется роль администратора.')
    return user


async def get_optional_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> User | None:
    """Возвращает пользователя, если токен валиден, иначе None."""
    if credentials is None or not credentials.credentials:
        return None
    try:
        payload = decode_access_token(credentials.credentials)
        user_id = int(payload['sub'])
    except (jwt.PyJWTError, KeyError, TypeError, ValueError):
        return None
    try:
        return await get_user(session, user_id)
    except Exception:
        return None
