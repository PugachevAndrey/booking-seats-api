from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User
from repositories.base import CRUDBase


class CRUDUser(CRUDBase[User]):
    """CRUD для пользователей."""

    async def get_by_login(
        self,
        session: AsyncSession,
        login: str,
    ) -> User | None:
        """Проверка логина (email или телефон)."""
        result = await session.execute(
            select(User).where(
                or_(
                    User.email == login,
                    User.phone == login,
                ),
            ),
        )
        return result.scalar_one_or_none()


user_crud = CRUDUser(User)
