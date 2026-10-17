from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from .base import MainSchema
from .booking_tables_slot import BookingTableSlot, BookingTableSlotShortInfo
from .cafe import CafeShortInfo
from .user import UserShortInfo


class BookingInfo(MainSchema):
    """Схема чтения бронирования."""

    id: int
    user: UserShortInfo
    cafe: CafeShortInfo
    tables_slots: BookingTableSlotShortInfo
    guest_number: int
    note: str | None
    status: str  # BookingStatus
    booking_date: date

    model_config = ConfigDict(from_attributes=True, extra='forbid')


class BookingCreate(BaseModel):
    """Схема создания бронирования."""

    cafe_id: int
    tables_slots: list[BookingTableSlot]
    guest_number: int
    note: str | None = Field(default=None)
    booking_date: date


class BookingUpdate(BaseModel):
    """Схема изменения бронирования."""

    tables_slots: list[BookingTableSlot] | None = Field(default=None)
    guest_number: int | None = Field(default=None)
    note: str | None = Field(default=None)
    status: str | None = Field(default=None)  # BookingStatus
    booking_date: date | None = Field(default=None)
    is_active: bool | None = Field(default=None)
