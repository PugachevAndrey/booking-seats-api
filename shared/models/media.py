"""Модель медиафайлов."""

import uuid

from sqlalchemy import UUID, String
from sqlalchemy.orm import Mapped, mapped_column

from shared.core.base_model import Base


class Media(Base):
    """Модуль медиафайлов."""

    __tablename__ = 'media'

    id: Mapped[uuid.UUID] = mapped_column(
        UUID,
        primary_key=True,
        default=uuid.uuid4,
        comment='ID медиафайла',
    )
    file_name: Mapped[str] = mapped_column(
        String(50),
        comment='Имя файла',
    )
