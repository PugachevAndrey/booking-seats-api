"""Модель слотов для бронирования."""

import uuid
from datetime import datetime

from sqlalchemy import UUID, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from src.core.base_model import Base


class Slot(Base):
    """Модель слотов."""

    cafe_id: Mapped[uuid.UUID] = mapped_column(
        UUID,
        ForeignKey('cafes.id'),
        comment='ID кафе',
    )
    start_time: Mapped[datetime] = mapped_column(
        DateTime,
        comment='Время начала слота',
    )
    end_time: Mapped[datetime] = mapped_column(
        DateTime,
        comment='Время завершения слота',
    )
    description: Mapped[str] = mapped_column(
        String(255),
        comment='Описание слота',
    )
