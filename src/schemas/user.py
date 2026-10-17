from datetime import datetime
from typing import Self

from pydantic import MISSING, BaseModel, ConfigDict, EmailStr, Field, model_validator
from pydantic_extra_types.phone_numbers import PhoneNumber

from .constants import MAX_LENGTH, MAX_TG_LENGTH, MAX_USERNAME_LENGTH, MIN_LENGTH
from src.core.enums import UserRole


class UserShortInfo(BaseModel):
    """Схема чтения мини-инфо о пользователе."""

    id: int
    username: str
    email: EmailStr | None
    phone: PhoneNumber | None
    tg_id: str | None

    model_config = ConfigDict(from_attributes=True, extra='forbid')


class UserInfo(UserShortInfo):
    """Схема чтения инфо о пользователе."""

    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, extra='forbid')


class UserCreate(BaseModel):
    """Схема создания пользователя."""

    username: str = Field(max_length=MAX_USERNAME_LENGTH)
    email: EmailStr | None = Field(max_length=MAX_LENGTH)
    phone: PhoneNumber | None = Field(max_length=MIN_LENGTH)
    tg_id: str | None = Field(max_length=MAX_TG_LENGTH)
    password: str = Field(max_length=MAX_LENGTH)

    @model_validator(mode='after')
    def check_login(self) -> Self:
        """Проверка наличия логина."""
        if self.email is None and self.phone is None:
            raise ValueError('Введите email или phone')
        return self


class UserUpdate(BaseModel):
    """Схема изменения пользователя."""

    username: str | MISSING = Field(max_length=MAX_USERNAME_LENGTH, default=MISSING)
    email: EmailStr | None | MISSING = Field(max_length=MAX_LENGTH, default=MISSING)
    phone: PhoneNumber | None | MISSING = Field(max_length=MIN_LENGTH, default=MISSING)
    tg_id: str | None | MISSING = Field(max_length=MAX_TG_LENGTH, default=MISSING)
    role: UserRole | MISSING = MISSING
    password: str | MISSING = Field(max_length=MAX_LENGTH, default=MISSING)
    is_active: bool | MISSING = MISSING
