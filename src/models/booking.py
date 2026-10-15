"""Модель бронирования."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from core.base_model import Base
from core.enums import BookingStatus


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
        comment='Количество гостей',
    )
    note: Mapped[str] = mapped_column(
        Text(),
        comment='Примечание',
    )
    status: Mapped[BookingStatus] = mapped_column(
        String(20),
        comment='Статус',
    )
    booking_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        comment='Дата и время бронирования',
    )

    __table_args__ = (
        Index(
            'ix_booking_cafe_id_booking_date',
            'cafe_id',
            'booking_date',
        ),
        Index(
            'ix_booking_user_id_booking_date',
            'user_id',
            'booking_date',
        ),
    )
