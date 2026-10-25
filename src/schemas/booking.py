"""Схемы бронирований."""

from datetime import date

from pydantic import MISSING, ConfigDict, Field

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
    note: str | None | MISSING = MISSING
    booking_date: date


class BookingUpdate(BaseSchema):
    """Схема изменения бронирования."""

    tables_slots: list[BookingTableSlot] | MISSING = Field(default=MISSING, min_length=MIN_SYMBOL)
    guest_number: int | MISSING = MISSING
    note: str | MISSING = MISSING
    status: BookingStatus | MISSING = MISSING
    booking_date: date | MISSING = MISSING
    is_active: bool | MISSING = MISSING
