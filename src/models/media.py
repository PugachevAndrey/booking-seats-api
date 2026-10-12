"""Модель медиафайлов."""

import uuid

from sqlalchemy import UUID, String
from sqlalchemy.orm import Mapped, mapped_column

from src.core.base_model import Base


class Media(Base):
    """Модуль медиафайлов."""

    __tablename__ = 'media'

    id: Mapped[uuid.UUID] = mapped_column(
        UUID,
        comment='ID медиафайла',
    )
    content_type: Mapped[str] = mapped_column(
        String(50),
        comment='Тип контента',
    )
