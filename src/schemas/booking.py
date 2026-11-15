"""Схемы бронирований."""

from datetime import date

from pydantic import ConfigDict, Field

from shared.core.enums import BookingStatus

from .base import BaseSchema, MainSchema
from .booking_tables_slot import BookingTableSlot, BookingTableSlotShortInfo
from .cafe import CafeShortInfo
from .constants import MIN_SYMBOL
from .user import UserShortInfo


class BookingInfo(MainSchema):
    """Схема чтения бронирования."""

    id: int
    user: UserShortInfo
    cafe: CafeShortInfo
    tables_slots: list[BookingTableSlotShortInfo]
    guest_number: int
    note: str | None
    status: BookingStatus
    booking_date: date

    model_config = ConfigDict(from_attributes=True, extra='forbid')


class BookingCreate(BaseSchema):
    """Схема создания бронирования."""

    cafe_id: int
    tables_slots: list[BookingTableSlot]
    guest_number: int
    note: str | None = None
    booking_date: date
    remind_before_minutes: int | None = None


class BookingUpdate(BaseSchema):
    """Схема изменения бронирования."""

    tables_slots: list[BookingTableSlot] | None = Field(
        default=None, min_length=MIN_SYMBOL,
    )
    guest_number: int | None = None
    note: str | None = None
    status: BookingStatus | None = None
    booking_date: date | None = None
    is_active: bool | None = None
    # reminder_task_id удален по замечанию наставника!
    remind_before_minutes: int | None = None
