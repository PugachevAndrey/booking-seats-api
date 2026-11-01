"""Репозиторий кафе."""

from repositories.base import CRUDBase
from shared.models.cafe import Cafe


class CRUDCafe(CRUDBase[Cafe]):
    """CRUD для кафе."""


cafe_crud = CRUDCafe(Cafe)
