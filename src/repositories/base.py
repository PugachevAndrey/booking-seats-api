"""Базовый CRUD-класс для репозиториев."""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

ModelType = TypeVar('ModelType')


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
        return await session.get(self.model, obj_id)

    async def get_multi(self, session: AsyncSession) -> list[ModelType]:
        """Получить все записи."""
        result = await session.execute(select(self.model))
        return list(result.scalars().all())

    async def get_by_attribute(
        self,
        session: AsyncSession,
        attribute: str,
        value: Any,
    ) -> ModelType | None:
        """Получить запись по указанному атрибуту."""
        column = getattr(self.model, attribute)
        result = await session.execute(
            select(self.model).where(column == value),
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        session: AsyncSession,
        obj_in: BaseModel,
    ) -> ModelType:
        """Создать новую запись."""
        db_obj = self.model(**obj_in.model_dump())
        session.add(db_obj)
        await session.flush()
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
        await session.flush()
        await session.refresh(db_obj)
        return db_obj
