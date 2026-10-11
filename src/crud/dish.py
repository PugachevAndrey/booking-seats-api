from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from crud.base import CRUDBase
from models.dish import Dish


class CRUDDish(CRUDBase[Dish]):
    async def get_by_cafe(
        self,
        session: AsyncSession,
        cafe_id: UUID,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Dish]:
        """Блюда конкретного кафе.

        Работает при условии, что в модели Dish есть поле cafe_id.
        Если связь many-to-many (одно блюдо в нескольких кафе) —
        метод надо переписать через join с таблицей связи.
        """
        stmt = (
            select(Dish)
            .where(Dish.cafe_id == cafe_id, Dish.is_active.is_(True))
            .offset(skip)
            .limit(limit)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())


dish_crud = CRUDDish(Dish)
