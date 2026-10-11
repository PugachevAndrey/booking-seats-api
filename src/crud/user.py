from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from crud.base import CRUDBase
from models.user import User


class CRUDUser(CRUDBase[User]):
    async def get_by_email(
        self, session: AsyncSession, email: str
    ) -> User | None:
        stmt = select(User).where(
            User.email == email,
            User.is_active.is_(True),
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_login(
        self, session: AsyncSession, login: str
    ) -> User | None:
        """Логин может быть email или phone."""
        stmt = select(User).where(
            or_(User.email == login, User.phone == login),
            User.is_active.is_(True),
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()


user_crud = CRUDUser(User)
