import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class CafeBase(BaseModel):
    """Базовая схема кафе."""

    name: str
    address: str
    phone: str
    description: Optional[str] = None
    photo_id: Optional[uuid.UUID] = None


class CafeCreate(CafeBase):
    """Схема создания кафе."""

    managers_id: list[int]


class CafeUpdate(BaseModel):
    """Схема обновления кафе."""

    name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    description: Optional[str] = None
    photo_id: Optional[uuid.UUID] = None
    managers_id: Optional[list[int]] = None
    is_active: Optional[bool] = None


class CafeInfo(CafeBase):
    """Информация о кафе."""

    id: int
    managers: list[dict] = []
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {'from_attributes': True}
