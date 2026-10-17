"""Модель кафе."""

import uuid

from sqlalchemy import UUID, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from core.base_model import Base


class Cafe(Base):
    """Модель кафе."""

    name: Mapped[str] = mapped_column(
        String(255),
        comment='Название кафе',
    )
    address: Mapped[str] = mapped_column(
        String(500),
        comment='Адрес кафе',
    )
    phone: Mapped[str] = mapped_column(
        String(20),
        comment='Телефон кафе',
    )
    description: Mapped[str] = mapped_column(
        Text(),
        comment='Описание кафе',
    )
    photo_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID,
        ForeignKey('media.id', ondelete='SET NULL'),
        unique=True,
        comment='ID фотографии',
    )
