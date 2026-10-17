from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from core.enums import UserRole


class UserBase(BaseModel):
    """Базовая схема пользователя."""

    username: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    tg_id: Optional[str] = None


class UserCreate(UserBase):
    """Схема для регистрации пользователя."""

    password: str = Field(..., min_length=6)


class UserUpdate(BaseModel):
    """Схема для обновления информации о пользователя."""

    username: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    tg_id: Optional[str] = None
    password: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


class UserInfo(UserBase):
    """Информация о пользователе."""

    id: int
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {'from_attributes': True}
