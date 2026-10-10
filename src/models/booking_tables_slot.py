"""Модель бронирования столов с указанием времени."""

import uuid

from sqlalchemy import UUID, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from src.core.base_model import Base


class BookingTablesSlot(Base):
    """Модель бронирования с временными слотами."""

    __tablename__ = 'booking_tables_slots'

    booking_id: Mapped[uuid.UUID] = mapped_column(
        UUID,
        ForeignKey('bookings.id'),
        comment='ID бронирования',
    )
    table_id: Mapped[uuid.UUID] = mapped_column(
        UUID,
        ForeignKey('tables.id'),
        comment='ID стола',
    )
    slot_id: Mapped[uuid.UUID] = mapped_column(
        UUID,
        ForeignKey('slots.id'),
        comment='ID временного слота',
    )
