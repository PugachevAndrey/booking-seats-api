"""Модель бронирования."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.core.base_model import Base


class Booking(Base):
    """Модель бронирования."""

    __tablename__ = 'booking'

    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('users.id'),
        comment='ID клиента',
    )
    cafe_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('cafes.id'),
        comment='ID кафе',
    )
    guest_number: Mapped[int] = mapped_column(
        Integer,
        comment='Номер клиента',
    )
    note: Mapped[str] = mapped_column(
        Text(),
        comment='Примечание',
    )
    status: Mapped[str] = mapped_column(
        String(20),
        comment='Статус',
    )
    booking_date: Mapped[datetime] = mapped_column(
        DateTime,
        comment='Дата и время бронирования',
    )
