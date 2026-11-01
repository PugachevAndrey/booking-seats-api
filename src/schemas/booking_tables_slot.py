"""Схемы бронирования столов с временными слотами."""

from pydantic import ConfigDict

from schemas.base import BaseSchema

from .slot import TimeSlotShortInfo
from .table import TableShortInfo


class BookingTableSlot(BaseSchema):
    """Схема для бронирования."""

    table_id: int
    slot_id: int


class BookingTableSlotShortInfo(BaseSchema):
    """Схема для инфо о бронировании."""

    table: TableShortInfo
    slot: TimeSlotShortInfo

    model_config = ConfigDict(from_attributes=True, extra='forbid')
