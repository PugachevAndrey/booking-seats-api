from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from crud.base import CRUDBase
from models.slot import Slot


class CRUDSlot(CRUDBase[Slot]):
    async def get_by_cafe(
        self,
        session: AsyncSession,
        cafe_id: UUID,
        *,
        skip: int = 0,
        limit: int = 100,
        only_active: bool = True,
    ) -> list[Slot]:
        stmt = select(Slot).where(Slot.cafe_id == cafe_id)
        if only_active:
            stmt = stmt.where(Slot.is_active.is_(True))
        stmt = stmt.offset(skip).limit(limit)
        result = await session.execute(stmt)
        return list(result.scalars().all())


slot_crud = CRUDSlot(Slot)
