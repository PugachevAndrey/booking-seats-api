from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from crud.base import CRUDBase
from models.table import Table


class CRUDTable(CRUDBase[Table]):
    async def get_by_cafe(
        self,
        session: AsyncSession,
        cafe_id: UUID,
        *,
        skip: int = 0,
        limit: int = 100,
        only_active: bool = True,
    ) -> list[Table]:
        stmt = select(Table).where(Table.cafe_id == cafe_id)
        if only_active:
            stmt = stmt.where(Table.is_active.is_(True))
        stmt = stmt.offset(skip).limit(limit)
        result = await session.execute(stmt)
        return list(result.scalars().all())


table_crud = CRUDTable(Table)
