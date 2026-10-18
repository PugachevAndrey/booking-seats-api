from datetime import time

from pydantic import MISSING, BaseModel, ConfigDict, Field

from .base import MainSchema
from .cafe import CafeShortInfo
from .constants import MAX_LENGTH


class TimeSlotShortInfo(BaseModel):
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


class TimeSlotCreate(BaseModel):
    """Схема создания временного слота."""

    start_time: time
    end_time: time
    description: str | None = Field(max_length=MAX_LENGTH)


class TableUpdate(BaseModel):
    """Схема изменения временного слота."""

    start_time: time | None | MISSING = MISSING
    end_time: time | None | MISSING = MISSING
    description: str | None | MISSING = Field(max_length=MAX_LENGTH, default=MISSING)
    is_active: bool | None | MISSING = MISSING
