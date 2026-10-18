"""Модель слотов для бронирования."""

from datetime import time

from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, String, Time
from sqlalchemy.orm import Mapped, mapped_column

from core.base_model import Base


class Slot(Base):
    """Модель слотов."""

    cafe_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('cafes.id'),
        comment='ID кафе',
    )
    start_time: Mapped[time] = mapped_column(
        Time,
        comment='Время начала слота',
    )
    end_time: Mapped[time] = mapped_column(
        Time,
        comment='Время завершения слота',
    )
    description: Mapped[str | None] = mapped_column(
        String(255),
        comment='Описание слота',
    )  # здесь поле не обязательное nullable = true

    __table_args__ = (
        Index(
            'ix_slots_cafe_id',
            'cafe_id',
        ),
        CheckConstraint(
            'end_time > start_time',
            name='ck_slots_end_time_after_start_time',
        ),
    )
