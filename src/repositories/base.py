from typing import Generic, TypeVar

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

ModelType = TypeVar("ModelType")


class CRUDBase(Generic[ModelType]):
    """Базовый CRUD-класс для работы с моделями."""

    def __init__(self, model: type[ModelType]) -> None:
        """Инициализация CRUD для указанной модели."""
        self.model = model

    async def get(
        self,
        session: AsyncSession,
        obj_id: int,
    ) -> ModelType | None:
        """Получить запись по id."""
        result = await session.execute(
            select(self.model).where(self.model.id == obj_id),
        )
        return result.scalar_one_or_none()

    async def get_multi(self, session: AsyncSession) -> list[ModelType]:
        """Получить все записи."""
        result = await session.execute(select(self.model))
        return list(result.scalars().all())

    async def create(
        self,
        session: AsyncSession,
        obj_in: BaseModel,
    ) -> ModelType:
        """Создать новую запись."""
        db_obj = self.model(**obj_in.model_dump())
        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)
        return db_obj

    async def update(
        self,
        session: AsyncSession,
        db_obj: ModelType,
        obj_in: BaseModel,
    ) -> ModelType:
        """Обновить существующую запись."""
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)
        return db_obj

    async def remove(
        self,
        session: AsyncSession,
        db_obj: ModelType,
    ) -> None:
        """Удалить запись."""
        await session.delete(db_obj)
        await session.commit()
