"""Модель пользователя."""

from pwdlib import PasswordHash
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from shared.core.base_model import Base
from shared.core.enums import UserRole

_hasher = PasswordHash.recommended()


class User(Base):
    """Модель пользователя."""

    username: Mapped[str] = mapped_column(
        String(100),
        unique=True,
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
        comment='Хэш пароля пользователя',
    )
    role: Mapped[UserRole] = mapped_column(
        String(20),
        default=UserRole.USER,
        comment='Роль пользователя',
    )

    @property
    def password(self) -> str:
        """Пароль в открытом виде не хранится - только хэш."""
        raise AttributeError(
            'Чтение пароля запрещено: он хранится только в виде хэша.',
        )

    @password.setter
    def password(self, password: str) -> None:
        """Хэширует и сохраняет пароль через set_password."""
        self.set_password(password)

    @staticmethod
    def hash_password(password: str) -> str:
        """Хэширует пароль."""
        return _hasher.hash(password)

    def set_password(self, password: str) -> None:
        """Хэширует пароль."""
        self.password_hash = self.hash_password(password)

    def check_password(self, password: str) -> bool:
        """Проверяет пароль и сохранённый хэш."""
        return _hasher.verify(password, self.password_hash)
