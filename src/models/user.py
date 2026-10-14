"""Модель пользователя."""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from core.base_model import Base


class User(Base):
    """Модель пользователя."""

    username: Mapped[str] = mapped_column(
        String(100),
        comment='Имя пользователя',
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        comment='Эл. почта пользователя',
    )
    phone: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        comment='Телефон пользователя',
    )
    tg_id: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        comment='ID Телеграмма пользователя',
    )
    password_hash: Mapped[str] = mapped_column(
        String(255),
        comment='Хэш пароля пользователя',
    )
    role: Mapped[str] = mapped_column(
        String(20),
        comment='Роль пользователя',
    )
