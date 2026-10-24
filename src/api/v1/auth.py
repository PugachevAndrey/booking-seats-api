from typing import Annotated

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.deps import get_db
from repositories.user import user_crud
from schemas.base import AuthSchema
from shared.core.errors import ValidationError
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
    user = await user_crud.get_by_login(
        login=data.login,
        session=session,
    )
    if user is None or not user.is_active:
        raise ValidationError('Неверный логин или пароль.')

    if not user.check_password(data.password.get_secret_value()):
        raise ValidationError('Неверный логин или пароль.')

    token = create_access_token(subject=user.id)
    return TokenResponse(access_token=token)
