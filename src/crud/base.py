from typing import Any, Generic, Sequence, Type, TypeVar
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.base_model import Base

ModelType = TypeVar("ModelType", bound=Base)


class CRUDBase(Generic[ModelType]):
    """Базовый CRUD-класс с типовыми операциями."""

    def __init__(self, model: Type[ModelType]) -> None:
        """Инициализация CRUD для конкретной модели."""
        self.model = model

    async def get(
        self,
        session: AsyncSession,
        obj_id: UUID,
        *,
        include_inactive: bool = False,
    ) -> ModelType | None:
        """Получить одну запись по id."""
        stmt = select(self.model).where(self.model.id == obj_id)
        if not include_inactive:
            stmt = stmt.where(self.model.is_active.is_(True))
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_multi(
        self,
        session: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
        include_inactive: bool = False,
        order_by: Any | None = None,
        **filters: Any,
    ) -> Sequence[ModelType]:
        """Получить список записей с пагинацией и фильтрами."""
        stmt = select(self.model)
        if not include_inactive:
            stmt = stmt.where(self.model.is_active.is_(True))
        for field, value in filters.items():
            if value is None:
                continue
            column = getattr(self.model, field, None)
            if column is None:
                raise AttributeError(
                    f"Модель {self.model.__name__} не имеет поля '{field}'",
                )
            stmt = stmt.where(column == value)
        if order_by is not None:
            stmt = stmt.order_by(order_by)
        stmt = stmt.offset(skip).limit(limit)
        result = await session.execute(stmt)
        return result.scalars().all()

    async def create(
        self,
        session: AsyncSession,
        **data: Any,
    ) -> ModelType:
        """Создать новую запись."""
        obj = self.model(**data)
        session.add(obj)
        await session.flush()
        await session.refresh(obj)
        return obj

    async def update(
        self,
        session: AsyncSession,
        obj: ModelType,
        **data: Any,
    ) -> ModelType:
        """Обновить существующую запись."""
        for field, value in data.items():
            setattr(obj, field, value)
        session.add(obj)
        await session.flush()
        await session.refresh(obj)
        return obj

    async def soft_delete(
        self,
        session: AsyncSession,
        obj: ModelType,
    ) -> ModelType:
        """Пометить запись как неактивную (is_active=False)."""
        obj.is_active = False
        session.add(obj)
        await session.flush()
        await session.refresh(obj)
        return obj
