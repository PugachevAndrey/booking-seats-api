"""Аутентификация: вход в систему и выдача JWT-токена."""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.deps import get_db
from api.validators import validate_login
from schemas.base import AuthSchema
from shared.core.security import create_access_token

router = APIRouter(prefix='/auth', tags=['Аутентификация'])


class TokenResponse(BaseModel):
    """Ответ с токеном."""

    access_token: str
    token_type: str = 'bearer'


@router.post(
    '/login',
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary='Получение токена авторизации',
    responses={
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            'description': 'Неверный логин или пароль',
        },
    },
)
async def login(
    data: AuthSchema,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    """Проверяет логин/пароль и возвращает JWT."""
    user = await validate_login(data, session)
    token = create_access_token(subject=user.id)
    return TokenResponse(access_token=token)
