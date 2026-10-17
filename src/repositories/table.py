from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.table import Table
from repositories.base import CRUDBase


class CRUDTable(CRUDBase[Table]):
    """CRUD для столов."""

    async def get_by_cafe(
        self,
        session: AsyncSession,
        cafe_id: int,
    ) -> list[Table]:
        """Получить столы кафе."""
        result = await session.execute(
            select(Table).where(Table.cafe_id == cafe_id),
        )
        return list(result.scalars().all())


table_crud = CRUDTable(Table)
