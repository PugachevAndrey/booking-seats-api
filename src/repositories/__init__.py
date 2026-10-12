"""Репозитории (CRUD-слой)."""

from repositories.action import action_crud
from repositories.booking import booking_crud
from repositories.cafe import cafe_crud
from repositories.dish import dish_crud
from repositories.media import media_crud
from repositories.slot import slot_crud
from repositories.table import table_crud
from repositories.user import user_crud

__all__: list[str] = []
