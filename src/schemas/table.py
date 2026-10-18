from pydantic import MISSING, ConfigDict, Field

from .base import BaseSchema, MainSchema
from .cafe import CafeShortInfo
from .constants import MAX_LENGTH


class TableShortInfo(BaseSchema):
    """Схема чтения мини-инфо о столе."""

    id: int
    description: str | None
    seat_number: int
    # response_model_exclude_none=True добавить в эндпойнт

    model_config = ConfigDict(from_attributes=True, extra='forbid')


class TableInfo(TableShortInfo, MainSchema):
    """Схема чтения инфо о столе."""

    cafe: CafeShortInfo

    model_config = ConfigDict(from_attributes=True, extra='forbid')


class TableCreate(BaseSchema):
    """Схема создания стола."""

    description: str | MISSING = Field(max_length=MAX_LENGTH, default=MISSING)
    seat_number: int


class TableUpdate(BaseSchema):
    """Схема изменения стола."""

    description: str | MISSING = MISSING
    seat_number: int | MISSING = MISSING
    is_active: bool | MISSING = MISSING
