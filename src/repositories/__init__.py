"""Репозитории (CRUD-слой)."""

from repositories.booking import booking_crud
from repositories.cafe import cafe_crud
from repositories.media import media_crud
from repositories.slot import slot_crud
from repositories.table import table_crud
from repositories.user import user_crud

__all__ = [
    "booking_crud",
    "cafe_crud",
    "media_crud",
    "slot_crud",
    "table_crud",
    "user_crud",
]
