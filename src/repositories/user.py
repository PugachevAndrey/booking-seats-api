from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User
from repositories.base import CRUDBase


class CRUDUser(CRUDBase[User]):
    """CRUD для пользователей."""

    async def get_by_email(
        self,
        session: AsyncSession,
        email: str,
    ) -> User | None:
        """Найти активного пользователя по email."""
        stmt = select(User).where(
            User.email == email,
            User.is_active.is_(True),
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_phone(
        self,
        session: AsyncSession,
        phone: str,
    ) -> User | None:
        """Найти активного пользователя по телефону."""
        stmt = select(User).where(
            User.phone == phone,
            User.is_active.is_(True),
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_login(
        self,
        session: AsyncSession,
        login: str,
    ) -> User | None:
        """Логин может быть email или phone."""
        stmt = select(User).where(
            or_(User.email == login, User.phone == login),
            User.is_active.is_(True),
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_managers_by_cafe(
        self,
        session: AsyncSession,
        cafe_id: UUID,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[User]:
        """Менеджеры конкретного кафе."""
        stmt = (
            select(User)
            .where(
                User.cafe_id == cafe_id,
                User.role == 'manager',
                User.is_active.is_(True),
            )
            .offset(skip)
            .limit(limit)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())


user_crud = CRUDUser(User)
