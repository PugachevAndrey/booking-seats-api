"""Модель бронирования столов с указанием времени."""

from sqlalchemy import ForeignKey, Index, Integer
from sqlalchemy.orm import Mapped, mapped_column

from shared.core.base_model import Base


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

    __table_args__ = (
        Index(
            'ix_booking_tables_slots_slot_id',
            'slot_id',
        ),
    )
