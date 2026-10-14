"""Модель слотов для бронирования."""

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String
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
        DateTime(timezone=True),
        comment='Время начала слота',
    )
    end_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        comment='Время завершения слота',
    )
    description: Mapped[str] = mapped_column(
        String(255),
        comment='Описание слота',
    )

    __table_args__ = (
        CheckConstraint(
            'start_time >= CURRENT_TIMESTAMP',
            name='ck_slots_start_time_not_in_past_time',
        ),
        CheckConstraint(
            'end_time > start_time',
            name='ck_slots_end_time_after_start_time',
        ),
    )
