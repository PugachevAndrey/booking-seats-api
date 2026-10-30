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
    """Сессия для Depends: возобновляет get_session, чтобы commit() выполнился."""
    cm = get_session()
    session = await cm.__aenter__()
    try:
        yield session
    finally:
        await cm.__aexit__(None, None, None)


DbSession = Annotated[AsyncSession, Depends(get_db, scope='function')]


def get_bearer_token(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> str:
    """Возвращает токен из заголовка или 401."""
    if credentials is None or not credentials.credentials:
        raise UnauthorizedError('Требуется авторизация.')
    return credentials.credentials


def decode_token(token: Annotated[str, Depends(get_bearer_token)]) -> dict:
    """Декодирует JWT или 401."""
    try:
        return decode_access_token(token)
    except jwt.PyJWTError:
        raise UnauthorizedError('Недействительный токен.')


def extract_user_id(payload: Annotated[dict, Depends(decode_token)]) -> int:
    """Достаёт sub из payload и приводит к int или 401."""
    subject = payload.get('sub')
    if subject is None:
        raise UnauthorizedError('Недействительный токен.')
    try:
        return int(subject)
    except (TypeError, ValueError):
        raise UnauthorizedError('Недействительный токен.')


async def get_current_user(
    user_id: Annotated[int, Depends(extract_user_id)],
    session: DbSession,
) -> User:
    """Возвращает пользователя по ID или 401, если не найден."""
    try:
        user = await get_user(session, user_id)
    except NotFoundError:
        raise UnauthorizedError('Недействительный токен.')
    if not user.is_active:
        raise UnauthorizedError('Пользователь заблокирован.')

    return user


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
    session: DbSession,
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
    except NotFoundError:
        return None
