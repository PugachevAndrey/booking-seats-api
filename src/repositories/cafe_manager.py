"""Репозиторий связей менеджеров с кафе."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from repositories.base import CRUDBase
from shared.models.cafe_manager import CafeManager


class CRUDCafeManager(CRUDBase[CafeManager]):
    """CRUD для связи менеджеров и кафе."""

    async def get_cafe_id_by_user(
        self,
        session: AsyncSession,
        user_id: int,
    ) -> int | None:
        """Получить ID кафе, к которому привязан менеджер."""
        result = await session.execute(
            select(CafeManager.cafe_id).where(CafeManager.user_id == user_id),
        )
        return result.scalar_one_or_none()


cafe_manager_crud = CRUDCafeManager(CafeManager)
