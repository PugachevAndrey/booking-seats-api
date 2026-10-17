from uuid import UUID

from pydantic import MISSING, BaseModel, ConfigDict, Field
from pydantic_extra_types.phone_numbers import PhoneNumber

from .base import MainSchema
from .constants import ADDRESS_LENGTH, MAX_LENGTH, MIN_LENGTH, MIN_SYMBOL
from .user import UserShortInfo


class CafeShortInfo(BaseModel):
    """Схема чтения мини-инфо о кафе."""

    id: int
    name: str
    address: str
    phone: PhoneNumber
    description: str | None
    photo_id: UUID | None

    model_config = ConfigDict(from_attributes=True, extra='forbid')


class CafeInfo(CafeShortInfo, MainSchema):
    """Схема чтения инфо о кафе."""

    managers: list[UserShortInfo]

    model_config = ConfigDict(from_attributes=True, extra='forbid')


class CafeCreate(BaseModel):
    """Схема создания кафе."""

    name: str = Field(min_length=MIN_SYMBOL, max_length=MAX_LENGTH)
    address: str = Field(min_length=MIN_SYMBOL, max_length=ADDRESS_LENGTH)
    phone: PhoneNumber = Field(min_length=MIN_SYMBOL, max_length=MIN_SYMBOL)
    description: str | None
    photo_id: UUID | None
    managers_id: list[int] = Field(min_length=MIN_SYMBOL)


class CafeUpdate(BaseModel):
    """Схема изменения кафе."""

    name: str | MISSING = Field(min_length=MIN_SYMBOL, max_length=MAX_LENGTH, default=MISSING)
    address: str | MISSING = Field(min_length=MIN_SYMBOL, max_length=ADDRESS_LENGTH, default=MISSING)
    phone: PhoneNumber | MISSING = Field(min_length=MIN_SYMBOL, max_length=MIN_LENGTH, default=MISSING)
    description: str | None | MISSING = MISSING
    photo_id: UUID | None | MISSING = MISSING
    managers_id: list[int] | MISSING = Field(min_length=MIN_SYMBOL, default=MISSING)
    is_active: bool | MISSING = MISSING
