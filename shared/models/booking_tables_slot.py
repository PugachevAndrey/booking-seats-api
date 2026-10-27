"""Модель бронирования столов с указанием времени."""

from sqlalchemy import ForeignKey, Index, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.core.base_model import Base
from shared.models.slot import Slot
from shared.models.table import Table


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
    table: Mapped[Table] = relationship(Table, lazy='selectin')
    slot_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('slots.id'),
        comment='ID временного слота',
    )
    slot: Mapped[Slot] = relationship(Slot, lazy='selectin')

    __table_args__ = (
        Index(
            'ix_booking_tables_slots_slot_id',
            'slot_id',
        ),
    )
