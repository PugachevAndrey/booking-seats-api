from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, SecretStr
from pydantic_extra_types.phone_numbers import PhoneNumber

from .constants import MAX_LENGTH


class AuthSchema(BaseModel):
    """Схема аутентификации."""

    login: str
    password: SecretStr = Field(MAX_LENGTH)

    model_config = ConfigDict(extra='forbid')


class MainSchema(BaseModel):
    """Общая схема."""

    is_active: bool
    created_at: datetime
    updated_at: datetime


class BaseSchema(BaseModel):
    """Общая схема для запрета лишних полей."""

    model_config = ConfigDict(extra='forbid')


class E164PhoneNumber(PhoneNumber):
    """Максимум 15 цифр, формат международного номера Е164."""

    phone_format = 'E164'
