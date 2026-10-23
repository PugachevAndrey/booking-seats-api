from typing import Self

from pydantic import MISSING, ConfigDict, EmailStr, Field, model_validator
from pydantic_extra_types.phone_numbers import PhoneNumber

from .base import BaseSchema, MainSchema
from .constants import MAX_LENGTH, MAX_TG_LENGTH, MAX_USERNAME_LENGTH, MIN_LENGTH, MIN_PASS
from core.enums import UserRole


class UserShortInfo(BaseSchema):
    """Схема чтения мини-инфо о пользователе."""

    id: int
    username: str
    email: EmailStr | None
    phone: PhoneNumber | None
    tg_id: str | None
    # response_model_exclude_none=True добавить в эндпойнт

    model_config = ConfigDict(from_attributes=True, extra='forbid')


class UserInfo(UserShortInfo, MainSchema):
    """Схема чтения инфо о пользователе."""

    role: UserRole

    model_config = ConfigDict(from_attributes=True, extra='forbid')


class UserCreate(BaseSchema):
    """Схема создания пользователя."""

    username: str = Field(max_length=MAX_USERNAME_LENGTH)
    email: EmailStr | MISSING = Field(max_length=MAX_LENGTH, default=MISSING)
    phone: PhoneNumber | MISSING = Field(max_length=MIN_LENGTH, default=MISSING)
    tg_id: str | MISSING = Field(max_length=MAX_TG_LENGTH, default=MISSING)
    password: str = Field(max_length=MAX_LENGTH, min_length=MIN_PASS)

    @model_validator(mode='after')
    def check_login(self) -> Self:
        """Проверка наличия email или phone."""
        if self.email is MISSING and self.phone is MISSING:
            raise ValueError('Введите email или phone')
        return self


class UserUpdate(BaseSchema):
    """Схема изменения пользователя."""

    username: str | MISSING = Field(max_length=MAX_USERNAME_LENGTH, default=MISSING)
    email: EmailStr | MISSING = Field(max_length=MAX_LENGTH, default=MISSING)
    phone: PhoneNumber | MISSING = Field(max_length=MIN_LENGTH, default=MISSING)
    tg_id: str | MISSING = Field(max_length=MAX_TG_LENGTH, default=MISSING)
    role: UserRole | MISSING = MISSING
    password: str | MISSING = Field(max_length=MAX_LENGTH, default=MISSING)
    is_active: bool | MISSING = MISSING
