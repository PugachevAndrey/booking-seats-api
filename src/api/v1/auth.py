from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix='/auth', tags=['Аутентификация'])


class LoginData(BaseModel):
    """Данные для входа."""

    login: str
    password: str


class TokenResponse(BaseModel):
    """Ответ с токеном."""

    access_token: str
    token_type: str


@router.post('/login', response_model=TokenResponse)
async def login(data: LoginData) -> TokenResponse:
    """Получение токена авторизации."""
    return TokenResponse(
        access_token='fake-jwt-token-for-now',
        token_type='bearer',
    )
