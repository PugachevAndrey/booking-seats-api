from pydantic import ConfigDict

from .slot import TimeSlotShortInfo
from .table import TableShortInfo
from src.schemas.base import BaseSchema


class BookingTableSlot(BaseSchema):
    """Схема для бронирования."""

    table_id: int
    slot_id: int


class BookingTableSlotShortInfo(BaseSchema):
    """Схема для инфо о бронировании."""

    table: TableShortInfo
    slot: TimeSlotShortInfo

    model_config = ConfigDict(from_attributes=True, extra='forbid')
