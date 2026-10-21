from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User
from services.access import is_admin, is_staff
from services.user import get_user

from core.db import get_session
from core.errors import PermissionDeniedError
from core.security import decode_access_token

bearer_scheme = HTTPBearer(auto_error=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Обёртка над `get_session` для `Depends`."""
    async with get_session() as session:
        yield session


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
    except Exception:
        raise PermissionDeniedError('Недействительный токен.')

    subject = payload.get('sub')
    if subject is None:
        raise PermissionDeniedError('Недействительный токен.')

    try:
        user_id = int(subject)
    except (TypeError, ValueError):
        raise PermissionDeniedError('Недействительный токен.')

    return await get_user(session, user_id)


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
    except Exception:
        return None
    try:
        return await get_user(session, user_id)
    except Exception:
        return None
