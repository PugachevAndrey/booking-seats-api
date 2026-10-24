from datetime import time
from typing import Self

from pydantic import MISSING, ConfigDict, Field, model_validator

from validators import validate_slot_time_range

from .base import BaseSchema, MainSchema
from .cafe import CafeShortInfo
from .constants import MAX_LENGTH


class TimeSlotShortInfo(BaseSchema):
    """Схема чтения мини-инфо о временном слоте."""

    id: int
    start_time: time
    end_time: time
    description: str | None

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
        if self.start_time is MISSING or self.end_time is MISSING:
            return self

        validate_slot_time_range(
            self.start_time,
            self.end_time,
        )
        return self


class TimeSlotUpdate(TimeSlotCreate):
    """Схема изменения временного слота."""

    start_time: time | MISSING = MISSING
    end_time: time | MISSING = MISSING
    is_active: bool | MISSING = MISSING
