from datetime import time
from typing import Self

from pydantic import MISSING, ConfigDict, Field, model_validator

from .base import BaseSchema, MainSchema
from .cafe import CafeShortInfo
from .constants import MAX_LENGTH


class TimeSlotShortInfo(BaseSchema):
    """Схема чтения мини-инфо о временном слоте."""

    id: int
    start_time: time
    end_time: time
    description: str | None
    # response_model_exclude_none=True добавить в эндпойнт

    model_config = ConfigDict(from_attributes=True, extra='forbid')


class TimeSlotInfo(TimeSlotShortInfo, MainSchema):
    """Схема чтения инфо о временном слоте."""

    cafe: CafeShortInfo

    model_config = ConfigDict(from_attributes=True, extra='forbid')


class TimeSlotCreate(BaseSchema):
    """Схема создания временного слота."""

    start_time: time
    end_time: time
    description: str | MISSING = Field(max_length=MAX_LENGTH, default=MISSING)

    @model_validator(mode='after')
    def validate_time(self) -> Self:
        """Проверка что время окончания не раньше времени начала."""
        if self.end_time <= self.start_time:
            raise ValueError('Время окончания бронирования должно быть позже времени начала.')
        return self


class TimeSlotUpdate(BaseSchema):
    """Схема изменения временного слота."""

    start_time: time | MISSING = MISSING
    end_time: time | MISSING = MISSING
    description: str | MISSING = Field(max_length=MAX_LENGTH, default=MISSING)
    is_active: bool | MISSING = MISSING