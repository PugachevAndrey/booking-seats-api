from http import HTTPStatus

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from repositories.user import user_crud
from schemas.base import AuthSchema


async def validate_login(
    auth_data: AuthSchema,
    session: AsyncSession,
) -> None:
    """Проверка логина и пароля."""
    user = await user_crud.get_by_login(login=auth_data.login, session=session)
    if user is None:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail='В поле login введите email или phone.',
        )
    if not user.check_password(password=auth_data.password):
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail='Неверные имя пользователя и пароль.',
        )
