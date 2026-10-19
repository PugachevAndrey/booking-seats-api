import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ActionBase(BaseModel):
    """Базовая схема акции."""

    description: str
    photo_id: Optional[uuid.UUID] = None


class ActionCreate(ActionBase):
    """Создание акции."""

    cafes_id: list[int]


class ActionUpdate(BaseModel):
    """Обновление акции."""

    description: Optional[str] = None
    photo_id: Optional[uuid.UUID] = None
    cafes_id: Optional[list[int]] = None
    is_active: Optional[bool] = None


class ActionInfo(ActionBase):
    """Информация об акции."""

    id: int
    cafes: list[dict]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {'from_attributes': True}
