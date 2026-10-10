"""Модель стола."""

import uuid

from sqlalchemy import UUID, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from src.core.base_model import Base


class Table(Base):
    """Модель стола."""

    cafe_id: Mapped[uuid.UUID] = mapped_column(
        UUID,
        ForeignKey('cafes.id'),
        comment='ID кафе',
    )
    description: Mapped[str] = mapped_column(
        String(255),
        comment='Описание слота',
    )
    seat_number: Mapped[int] = mapped_column(
        Integer,
        comment='Номер сидения',
    )
