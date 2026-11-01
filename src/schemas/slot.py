"""Схемы временных слотов."""

from datetime import time
from typing import Any, Self

from pydantic import (
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

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
    description: str | None = Field(default=None, max_length=MAX_LENGTH)

    @field_validator('start_time', 'end_time')
    @classmethod
    def _strip_tz(cls, v: time) -> time:
        """Слот — wall-clock время кафе; 'Z'/offset отбрасываем.

        Колонка в БД — TIME WITHOUT TIME ZONE, поэтому aware-time
        нужно нормализовать до записи, иначе asyncpg падает.
        """
        if v.tzinfo is not None:
            v = v.replace(tzinfo=None)
        return v

    @model_validator(mode='after')
    def validate_time(self) -> Self:
        """Проверка что время окончания не раньше времени начала."""
        validate_slot_time_range(
            self.start_time,
            self.end_time,
        )
        return self


class TimeSlotUpdate(BaseSchema):
    """Схема изменения временного слота."""

    start_time: time | None = None
    end_time: time | None = None
    description: str | None = Field(default=None, max_length=MAX_LENGTH)
    is_active: bool | None = None

    @model_validator(mode='before')
    @classmethod
    def _reject_explicit_nulls(cls, data: Any) -> Any:
        """Отклоняем явный null для NOT NULL-полей (422 вместо 500)."""
        if isinstance(data, dict):
            for field in ('start_time', 'end_time', 'is_active'):
                if field in data and data[field] is None:
                    raise ValueError(f'{field} не может быть null.')
        return data

    @field_validator('start_time', 'end_time')
    @classmethod
    def _strip_tz(cls, v: time | None) -> time | None:
        """Нормализация aware-time для PATCH-запроса."""
        if v is not None and v.tzinfo is not None:
            v = v.replace(tzinfo=None)
        return v

    @model_validator(mode='after')
    def validate_time(self) -> Self:
        """Проверка, если переданы оба поля."""
        if self.start_time is not None and self.end_time is not None:
            validate_slot_time_range(self.start_time, self.end_time)
        return self
