"""Репозиторий связей менеджеров с кафе."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from repositories.base import CRUDBase
from shared.models.cafe_manager import CafeManager
from shared.models.user import User


class CRUDCafeManager(CRUDBase[CafeManager]):
    """CRUD для связи менеджеров и кафе."""

    async def get_manager_ids_by_cafe(
        self,
        session: AsyncSession,
        cafe_id: int,
    ) -> list[int]:
        """Получить ID активных менеджеров кафе."""
        result = await session.execute(
            select(CafeManager.user_id)
            .where(
                CafeManager.cafe_id == cafe_id,
                CafeManager.is_active.is_(True),
            )
            .order_by(CafeManager.user_id),
        )
        return list(result.scalars().all())

    async def get_link(
        self,
        session: AsyncSession,
        cafe_id: int,
        user_id: int,
    ) -> CafeManager | None:
        """Получить активную связь менеджера с кафе."""
        result = await session.execute(
            select(CafeManager).where(
                CafeManager.user_id == user_id,
                CafeManager.cafe_id == cafe_id,
                CafeManager.is_active.is_(True),
            ),
        )
        return result.scalar_one_or_none()

    async def get_any_link(
        self,
        session: AsyncSession,
        cafe_id: int,
        user_id: int,
    ) -> CafeManager | None:
        """Получить связь независимо от активности."""
        result = await session.execute(
            select(CafeManager).where(
                CafeManager.user_id == user_id,
                CafeManager.cafe_id == cafe_id,
            ),
        )
        return result.scalar_one_or_none()

    async def get_link_by_user(
        self,
        session: AsyncSession,
        user_id: int,
    ) -> CafeManager | None:
        """Получить любую связь менеджера по user_id."""
        result = await session.execute(
            select(CafeManager).where(CafeManager.user_id == user_id),
        )
        return result.scalar_one_or_none()

    async def get_existing_user_ids(
        self,
        session: AsyncSession,
        user_ids: list[int],
    ) -> set[int]:
        """Получить ID существующих активных пользователей из списка."""
        if not user_ids:
            return set()
        result = await session.execute(
            select(User.id).where(
                User.id.in_(user_ids),
                User.is_active.is_(True),
            ),
        )
        return set(result.scalars().all())

    async def get_busy_user_ids(
        self,
        session: AsyncSession,
        user_ids: list[int],
        exclude_cafe_id: int | None = None,
    ) -> set[int]:
        """Получить ID менеджеров, привязанных к другим кафе."""
        if not user_ids:
            return set()
        query = select(CafeManager.user_id).where(
            CafeManager.user_id.in_(user_ids),
            CafeManager.is_active.is_(True),
        )
        if exclude_cafe_id is not None:
            query = query.where(CafeManager.cafe_id != exclude_cafe_id)
        result = await session.execute(query)
        return set(result.scalars().all())

    async def get_cafe_id_by_user(
        self,
        session: AsyncSession,
        user_id: int,
    ) -> int | None:
        """Получить ID кафе активной привязки менеджера."""
        result = await session.execute(
            select(CafeManager.cafe_id).where(
                CafeManager.user_id == user_id,
                CafeManager.is_active.is_(True),
            ),
        )
        return result.scalar_one_or_none()

    async def get_managers_by_cafe(
        self,
        session: AsyncSession,
        cafe_id: int,
    ) -> list[CafeManager]:
        """Получить активных менеджеров кафе.

        Благодаря lazy="selectin" в модели, объекты user и cafe
        уже будут загружены и доступны через manager.user и manager.cafe.
        """
        result = await session.execute(
            select(CafeManager).where(
                CafeManager.cafe_id == cafe_id,
                CafeManager.is_active.is_(True),
            )
            .options(
                selectinload(CafeManager.user),
                selectinload(CafeManager.cafe),
            ),
        )
        return list(result.scalars().all())


cafe_manager_crud = CRUDCafeManager(CafeManager)
