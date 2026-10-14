from pydantic import BaseModel, ConfigDict

from .slot import TimeSlotShortInfo
from .table import TableShortInfo


class BookingTableSlot(BaseModel):
    """Схема для бронирования."""

    table_id: int
    slot_id: int


class BookingTableSlotShortInfo(BaseModel):
    """Схема для инфо о бронировании."""

    table: TableShortInfo
    slot: TimeSlotShortInfo

    model_config = ConfigDict(from_attributes=True, extra='forbid')
