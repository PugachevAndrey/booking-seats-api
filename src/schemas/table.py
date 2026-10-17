from pydantic import MISSING, BaseModel, ConfigDict, Field

from .base import MainSchema
from .cafe import CafeShortInfo
from .constants import MAX_LENGTH


class TableShortInfo(BaseModel):
    """Схема чтения мини-инфо о столе."""

    id: int
    description: str | None
    seat_number: int

    model_config = ConfigDict(from_attributes=True, extra='forbid')


class TableInfo(TableShortInfo, MainSchema):
    """Схема чтения инфо о столе."""

    cafe: CafeShortInfo

    model_config = ConfigDict(from_attributes=True, extra='forbid')


class TableCreate(BaseModel):
    """Схема создания стола."""

    description: str | None = Field(max_length=MAX_LENGTH)
    seat_number: int


class TableUpdate(BaseModel):
    """Схема изменения стола."""

    description: str | None | MISSING = MISSING
    seat_number: int | MISSING = MISSING
    is_active: bool | MISSING = MISSING
