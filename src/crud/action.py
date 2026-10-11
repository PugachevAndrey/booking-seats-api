from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from crud.base import CRUDBase
from models.action import Action


class CRUDAction(CRUDBase[Action]):
    async def get_active_by_cafe(
        self,
        session: AsyncSession,
        cafe_id: UUID,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Action]:
        stmt = (
            select(Action)
            .where(Action.cafe_id == cafe_id, Action.is_active.is_(True))
            .offset(skip)
            .limit(limit)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())


action_crud = CRUDAction(Action)
