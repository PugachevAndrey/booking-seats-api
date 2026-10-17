from datetime import datetime, time
from typing import Optional

from pydantic import BaseModel


class SlotBase(BaseModel):
    """Базовая схема слота."""

    start_time: time
    end_time: time
    description: Optional[str] = None


class SlotCreate(SlotBase):
    """Создание слота."""

    pass


class SlotUpdate(BaseModel):
    """Обновление слота."""

    start_time: Optional[time] = None
    end_time: Optional[time] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class SlotInfo(SlotBase):
    """Информация о слоте."""

    id: int
    cafe: dict
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {'from_attributes': True}
