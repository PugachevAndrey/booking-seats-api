"""Репозиторий временных слотов."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from repositories.base import CRUDBase
from shared.models.slot import Slot


class CRUDSlot(CRUDBase[Slot]):
    """CRUD для слотов времени."""

    async def get_by_cafe(
        self,
        session: AsyncSession,
        cafe_id: int,
    ) -> list[Slot]:
        """Получить слоты кафе."""
        result = await session.execute(
            select(Slot).where(Slot.cafe_id == cafe_id),
        )
        return list(result.scalars().all())


slot_crud = CRUDSlot(Slot)
