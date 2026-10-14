from datetime import datetime

from pydantic import BaseModel, Field, SecretStr

from .constants import MAX_LENGTH


class AuthSchema(BaseModel):
    """Схема аутентификации."""

    login: str
    password: SecretStr = Field(MAX_LENGTH)


class MainSchema(BaseModel):
    """Общая схема."""

    is_active: bool
    created_at: datetime
    updated_at: datetime | None
