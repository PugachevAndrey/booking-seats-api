"""Схемы столиков."""

from pydantic import ConfigDict, Field

from .base import BaseSchema, MainSchema
from .cafe import CafeShortInfo
from .constants import MAX_LENGTH


class TableShortInfo(BaseSchema):
    """Краткая информация о столике."""

    id: int
    description: str | None
    seat_number: int

    model_config = ConfigDict(from_attributes=True, extra='forbid')


class TableInfo(TableShortInfo, MainSchema):
    """Полная информация о столике."""

    cafe: CafeShortInfo

    model_config = ConfigDict(from_attributes=True, extra='forbid')


class TableCreate(BaseSchema):
    """Схема создания столика."""

    description: str | None = Field(default=None, max_length=MAX_LENGTH)
    seat_number: int


class TableUpdate(BaseSchema):
    """Схема обновления столика."""

    description: str | None = Field(default=None, max_length=MAX_LENGTH)
    seat_number: int | None = None
    is_active: bool | None = None
