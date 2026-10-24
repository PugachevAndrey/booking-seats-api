from models.user import User
from sqlalchemy.ext.asyncio import AsyncSession

from repositories.user import user_crud
from schemas.base import AuthSchema
from shared.core.errors import ValidationError


async def validate_login(
    auth_data: AuthSchema,
    session: AsyncSession,
) -> User:
    """Проверка логина и пароля. При неудаче — ValidationError (422)."""
    user = await user_crud.get_by_login(login=auth_data.login, session=session)
    if user is None or not user.is_active:
        raise ValidationError('Неверный логин или пароль.')
    if not user.check_password(auth_data.password.get_secret_value()):
        raise ValidationError('Неверный логин или пароль.')
    return user
