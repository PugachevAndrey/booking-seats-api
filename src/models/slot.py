"""Модель слотов для бронирования."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from core.base_model import Base


class Slot(Base):
    """Модель слотов."""

    cafe_id: Mapped[int] = mapped_column(
        Integer,
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
