from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel

from core.enums import BookingStatus


class BookingTableSlot(BaseModel):
    """Бронирования столика в слот."""

    table_id: int
    slot_id: int


class BookingCreate(BaseModel):
    """Создание бронирования."""

    cafe_id: int
    tables_slots: list[BookingTableSlot]
    guest_number: int
    note: Optional[str] = None
    booking_date: date


class BookingUpdate(BaseModel):
    """Обновление бронирования."""

    tables_slots: Optional[list[BookingTableSlot]] = None
    guest_number: Optional[int] = None
    note: Optional[str] = None
    status: Optional[BookingStatus] = None
    booking_date: Optional[date] = None
    is_active: Optional[bool] = None


class BookingInfo(BaseModel):
    """Информация о бронировании."""

    id: int
    user: dict
    cafe: dict
    tables_slots: list[dict]
    guest_number: int
    note: Optional[str]
    status: BookingStatus
    booking_date: date
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {'from_attributes': True}
