from uuid import UUID

from models.dish import Dish
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from repositories.base import CRUDBase


class CRUDDish(CRUDBase[Dish]):
    """CRUD для блюд."""

    async def get_by_cafe(
        self,
        session: AsyncSession,
        cafe_id: UUID,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Dish]:
        """Блюда конкретного кафе."""
        stmt = (
            select(Dish)
            .where(Dish.cafe_id == cafe_id, Dish.is_active.is_(True))
            .offset(skip)
            .limit(limit)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())


dish_crud = CRUDDish(Dish)
