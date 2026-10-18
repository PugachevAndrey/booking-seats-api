from datetime import date

from pydantic import MISSING, BaseModel, ConfigDict, Field

from .base import MainSchema
from .booking_tables_slot import BookingTableSlot, BookingTableSlotShortInfo
from .cafe import CafeShortInfo
from .constants import MIN_SYMBOL
from .user import UserShortInfo
from src.core.enums import BookingStatus


class BookingInfo(MainSchema):
    """Схема чтения бронирования."""

    id: int
    user: UserShortInfo
    cafe: CafeShortInfo
    tables_slots: BookingTableSlotShortInfo
    guest_number: int
    note: str | None
    status: BookingStatus
    booking_date: date

    model_config = ConfigDict(from_attributes=True, extra='forbid')


class BookingCreate(BaseModel):
    """Схема создания бронирования."""

    cafe_id: int
    tables_slots: list[BookingTableSlot]
    guest_number: int
    note: str | None
    booking_date: date


class BookingUpdate(BaseModel):
    """Схема изменения бронирования."""

    tables_slots: list[BookingTableSlot] | MISSING = Field(default=MISSING, min_length=MIN_SYMBOL)
    guest_number: int | MISSING = MISSING
    note: str | None | MISSING = MISSING
    status: BookingStatus | MISSING = MISSING
    booking_date: date | MISSING = MISSING
    is_active: bool | MISSING = MISSING
