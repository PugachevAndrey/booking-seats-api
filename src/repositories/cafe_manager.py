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

    async def get_managers_by_cafe(
        self,
        session: AsyncSession,
        cafe_id: int,
    ) -> list[CafeManager]:
        """
        Получить менеджеров кафе.

        Благодаря lazy="selectin" в модели, объекты user и cafe
        уже будут загружены и доступны через manager.user и manager.cafe.
        """
        result = await session.execute(
            select(CafeManager).where(CafeManager.cafe_id == cafe_id),
        )
        return list(result.scalars().all())


cafe_manager_crud = CRUDCafeManager(CafeManager)
