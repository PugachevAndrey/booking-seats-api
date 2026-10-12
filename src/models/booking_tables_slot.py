"""Модель бронирования столов с указанием времени."""

from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from core.base_model import Base


class BookingTablesSlot(Base):
    """Модель бронирования с временными слотами."""

    __tablename__ = 'booking_tables_slots'

    booking_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('booking.id'),
        comment='ID бронирования',
    )
    table_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('tables.id'),
        comment='ID стола',
    )
    slot_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('slots.id'),
        comment='ID временного слота',
    )
