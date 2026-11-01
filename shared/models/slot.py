"""Модель слотов для бронирования."""

from datetime import time

from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, String, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.core.base_model import Base
from shared.models.cafe import Cafe


class Slot(Base):
    """Модель слотов."""

    cafe_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('cafes.id'),
        comment='ID кафе',
    )
    cafe: Mapped[Cafe] = relationship(Cafe, lazy='selectin')
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
    )

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
