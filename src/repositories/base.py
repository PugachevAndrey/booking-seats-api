from typing import Any
from uuid import UUID

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class CRUDBase:
    """Базовый класс для CRUD операций."""

    def __init__(self, model: Any) -> None:
        """Инициализация CRUD."""
        self.model = model

    async def get(
        self,
        obj_id: UUID,
        session: AsyncSession,
    ) -> Any:
        """Получить одну запись по ID."""
        db_obj = await session.execute(
            select(self.model).where(self.model.id == obj_id),
        )
        return db_obj.scalars().first()

    async def get_multi(
        self,
        session: AsyncSession,
    )-> list[Any]:
        """Получить все записи."""
        db_objs = await session.execute(select(self.model))
        return db_objs.scalars().all()

    async def create(
        self,
        obj_in: BaseModel,
        session: AsyncSession,
        user: Any = None,
    ) -> Any:
        """Создать новую запись."""
        obj_in_data = obj_in.model_dump()
        if user is not None:
            obj_in_data['user_id'] = user.id
        db_obj = self.model(**obj_in_data)
        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)
        return db_obj

    async def update(
        self,
        db_obj: Any,
        obj_in: BaseModel,
        session: AsyncSession,
    ) -> Any:
        """Обновить существующую запись."""
        obj_data = jsonable_encoder(db_obj)
        update_data = obj_in.model_dump(exclude_unset=True)

        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])

        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)
        return db_obj

    async def remove(
        self,
        db_obj: Any,
        session: AsyncSession,
    ) -> Any:
        """Удалить запись."""
        await session.delete(db_obj)
        await session.commit()
        return db_obj
