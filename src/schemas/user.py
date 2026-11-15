"""Схемы пользователей."""

from typing import Self

from pydantic import ConfigDict, EmailStr, Field, SecretStr, model_validator

from shared.core.enums import UserRole

from .base import BaseSchema, MainSchema
from .constants import MAX_LENGTH, MAX_TG_LENGTH, MAX_USERNAME_LENGTH, MIN_SYMBOL, StrictPhoneNumber


class UserShortInfo(BaseSchema):
    """Краткая информация о пользователе."""

    id: int
    username: str

    model_config = ConfigDict(from_attributes=True, extra='forbid')


class UserInfo(UserShortInfo, MainSchema):
    """Полная информация о пользователе."""

    email: EmailStr | None
    phone: StrictPhoneNumber | None
    tg_id: str | None
    role: UserRole
    is_active: bool

    model_config = ConfigDict(from_attributes=True, extra='forbid')


class UserCreate(BaseSchema):
    """Схема создания пользователя."""

    username: str = Field(
        min_length=MIN_SYMBOL, max_length=MAX_USERNAME_LENGTH,
    )
    email: EmailStr | None = Field(default=None, max_length=MAX_LENGTH)
    phone: StrictPhoneNumber | None = None
    tg_id: str | None = Field(default=None, max_length=MAX_TG_LENGTH)
    password: SecretStr

    @model_validator(mode='after')
    def check_email_or_phone(self) -> Self:
        """Нужен хотя бы email или телефон."""
        if self.email is None and self.phone is None:
            raise ValueError('Нужен email или телефон.')
        return self


class UserUpdate(BaseSchema):
    """Схема обновления пользователя."""

    username: str | None = Field(default=None, max_length=MAX_USERNAME_LENGTH)
    email: EmailStr | None = Field(default=None, max_length=MAX_LENGTH)
    phone: StrictPhoneNumber | None = None
    tg_id: str | None = Field(default=None, max_length=MAX_TG_LENGTH)
    role: UserRole | None = None
    password: SecretStr | None = None
    is_active: bool | None = None
