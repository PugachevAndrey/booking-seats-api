"""Репозиторий пользователей."""

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from repositories.base import CRUDBase
from shared.models.cafe_manager import CafeManager
from shared.models.user import User


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
                    # User.username == login,
                ),
            ),
        )
        return result.scalar_one_or_none()

    async def get_by_cafe_id(
        self,
        session: AsyncSession,
        cafe_id: int,
    ) -> list[User]:
        """Получить активных менеджеров кафе."""
        result = await session.execute(
            select(User)
            .join(CafeManager, CafeManager.user_id == User.id)
            .where(
                CafeManager.cafe_id == cafe_id,
                CafeManager.is_active.is_(True),
                User.is_active.is_(True),
            )
            .order_by(User.id),
        )
        return list(result.scalars().all())

    async def get_ids_by_attributes(
        self,
        session: AsyncSession,
        email: str | None = None,
        phone: str | None = None,
        tg_id: str | None = None,
        exclude_user_id: int | None = None,
    ) -> list[int]:
        """Найти ID пользователей по совпадению email, phone или tg_id."""
        conditions = []
        if email is not None:
            conditions.append(User.email == email)
        if phone is not None:
            conditions.append(User.phone == phone)
        if tg_id is not None:
            conditions.append(User.tg_id == tg_id)
        if not conditions:
            return []

        query = select(User.id).where(or_(*conditions))
        if exclude_user_id is not None:
            query = query.where(User.id != exclude_user_id)
        result = await session.execute(query)
        return list(result.scalars().all())


user_crud = CRUDUser(User)
