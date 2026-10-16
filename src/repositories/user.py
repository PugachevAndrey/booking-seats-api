from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User
from repositories.base import CRUDBase


class CRUDUser(CRUDBase[User]):
    """CRUD для пользователей."""

    async def get_by_attribute(
        self,
        session: AsyncSession,
        attribute: str,
        value: str,
    ) -> User | None:
        """Получить пользователя по указанному атрибуту."""
        column = getattr(User, attribute)
        result = await session.execute(
            select(User).where(column == value),
        )
        return result.scalar_one_or_none()

    async def get_managers_by_cafe(
        self,
        session: AsyncSession,
        cafe_id: int,
    ) -> list[User]:
        """Получить менеджеров кафе."""
        result = await session.execute(
            select(User).where(
                User.cafe_id == cafe_id,
                User.role == "manager",
            ),
        )
        return list(result.scalars().all())


user_crud = CRUDUser(User)
