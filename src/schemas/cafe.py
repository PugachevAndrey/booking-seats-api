"""Схемы кафе."""

from typing import Self
from uuid import UUID

from pydantic import ConfigDict, Field, model_validator

from .base import BaseSchema, MainSchema
from .constants import ADDRESS_LENGTH, MAX_LENGTH, MIN_SYMBOL, StrictPhoneNumber
from .user import UserShortInfo


class CafeShortInfo(BaseSchema):
    """Краткая информация о кафе."""

    id: int
    name: str
    address: str
    phone: StrictPhoneNumber
    description: str | None
    photo_id: UUID | None

    model_config = ConfigDict(from_attributes=True, extra='forbid')


class CafeInfo(CafeShortInfo, MainSchema):
    """Полная информация о кафе."""

    managers: list[UserShortInfo] = []

    model_config = ConfigDict(from_attributes=True, extra='forbid')


class CafeCreate(BaseSchema):
    """Схема создания кафе."""

    name: str = Field(min_length=MIN_SYMBOL, max_length=MAX_LENGTH)
    address: str = Field(min_length=MIN_SYMBOL, max_length=ADDRESS_LENGTH)
    phone: StrictPhoneNumber
    description: str | None = None
    photo_id: UUID | None = None
    managers_id: list[int] = Field(default_factory=list)


class CafeUpdate(BaseSchema):
    """Схема обновления кафе."""

    name: str | None = Field(
        default=None, min_length=MIN_SYMBOL, max_length=MAX_LENGTH,
    )
    address: str | None = Field(
        default=None, min_length=MIN_SYMBOL, max_length=ADDRESS_LENGTH,
    )
    phone: StrictPhoneNumber | None = None
    description: str | None = None
    photo_id: UUID | None = None
    managers_id: list[int] | None = Field(default=None, min_length=MIN_SYMBOL)
    is_active: bool | None = None

    @model_validator(mode='after')
    def check_empty_update(self) -> Self:
        """Проверяет, что передан хотя бы один параметр."""
        if not self.model_fields_set:
            raise ValueError(
                'Нужно передать хотя бы одно поле для обновления.',
            )
        return self
