"""Модель медиафайлов."""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from src.core.base_model import Base


class Media(Base):
    """Модуль медиафайлов."""

    __tablename__ = 'media'

    content_type: Mapped[str] = mapped_column(
        String(50),
        comment='Тип контента',
    )
