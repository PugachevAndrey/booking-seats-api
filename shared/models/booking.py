"""Модель бронирования."""

from datetime import date

from sqlalchemy import Date, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.core.base_model import Base
from shared.core.enums import BookingStatus
from shared.models.booking_tables_slot import BookingTablesSlot
from shared.models.cafe import Cafe
from shared.models.user import User


class Booking(Base):
    """Модель бронирования."""

    __tablename__ = 'booking'

    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('users.id'),
        comment='ID клиента',
    )
    user: Mapped[User] = relationship(User, lazy='selectin')
    cafe_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('cafes.id'),
        comment='ID кафе',
    )
    cafe: Mapped[Cafe] = relationship(Cafe, lazy='selectin')
    guest_number: Mapped[int] = mapped_column(
        Integer,
        comment='Количество гостей',
    )
    note: Mapped[str | None] = mapped_column(
        Text(),
        comment='Примечание',
    )
    status: Mapped[BookingStatus] = mapped_column(
        String(20),
        comment='Статус',
    )
    booking_date: Mapped[date] = mapped_column(
        Date,
        comment='Дата бронирования',
    )
    tables_slots: Mapped[list[BookingTablesSlot]] = relationship(
        BookingTablesSlot,
        lazy='selectin',
        order_by=BookingTablesSlot.id,
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

    remind_before_minutes: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment='За сколько минут напомнить',
    )
    reminder_task_id: Mapped[str | None] = mapped_column(
        String(155),
        nullable=True,
        comment='ID задачи Celery',
    )
