"""Модель пользователя."""

from pwdlib import PasswordHash
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from core.base_model import Base
from core.enums import UserRole


class User(Base):
    """Модель пользователя."""

    username: Mapped[str] = mapped_column(
        String(100),
        comment='Имя пользователя',
    )
    email: Mapped[str | None] = mapped_column(
        String(255),
        unique=True,
        comment='Эл. почта пользователя',
    )
    phone: Mapped[str | None] = mapped_column(
        String(20),
        unique=True,
        comment='Телефон пользователя',
    )
    tg_id: Mapped[str | None] = mapped_column(
        String(50),
        unique=True,
        comment='ID Телеграмма пользователя',
    )
    password_hash: Mapped[str] = mapped_column(
        String(255),
        default=PasswordHash.recommended,
        comment='Хэш пароля пользователя',
    )
    role: Mapped[UserRole] = mapped_column(
        String(20),
        default=UserRole.USER,
        comment='Роль пользователя',
    )
