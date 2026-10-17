import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class DishBase(BaseModel):
    """Базовая схема блюда."""

    name: str
    description: Optional[str] = None
    photo_id: Optional[uuid.UUID] = None
    price: float


class DishCreate(DishBase):
    """Создание блюда."""

    cafes_id: list[int]


class DishUpdate(BaseModel):
    """Обновление блюда."""

    name: Optional[str] = None
    description: Optional[str] = None
    photo_id: Optional[uuid.UUID] = None
    price: Optional[float] = None
    cafes_id: Optional[list[int]] = None
    is_active: Optional[bool] = None


class DishInfo(DishBase):
    """Информация о блюде."""

    id: int
    cafes: list[dict]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {'from_attributes': True}
