from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class TableBase(BaseModel):
    """Базовая схема столика."""

    description: Optional[str] = None
    seat_number: int


class TableCreate(TableBase):
    """Создание столика."""

    pass


class TableUpdate(BaseModel):
    """Обновление столика."""

    description: Optional[str] = None
    seat_number: Optional[int] = None
    is_active: Optional[bool] = None


class TableInfo(TableBase):
    """Информация о столике."""

    id: int
    cafe: dict
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {'from_attributes': True}
