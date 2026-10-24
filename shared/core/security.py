"""Создание и проверка JWT-токенов."""

from datetime import datetime, timedelta, timezone
from typing import Any

import jwt

from shared.core.settings import settings


def create_access_token(
    subject: str | int,
    expires_minutes: int | None = None,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """Создаёт JWT access-токен."""
    expire_minutes = expires_minutes or settings.access_token_expire_minutes
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        'sub': str(subject),
        'iat': int(now.timestamp()),
        'exp': int((now + timedelta(minutes=expire_minutes)).timestamp()),
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    """Декодирует и проверяет JWT. Бросает `jwt.PyJWTError` при ошибке."""
    return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
