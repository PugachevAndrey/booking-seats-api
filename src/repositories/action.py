from uuid import UUID

from models.action import Action
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from repositories.base import CRUDBase


class CRUDAction(CRUDBase[Action]):
    """CRUD для акций."""

    async def get_active_by_cafe(
        self,
        session: AsyncSession,
        cafe_id: UUID,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Action]:
        """Активные акции конкретного кафе."""
        stmt = (
            select(Action)
            .where(Action.cafe_id == cafe_id, Action.is_active.is_(True))
            .offset(skip)
            .limit(limit)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())


action_crud = CRUDAction(Action)
