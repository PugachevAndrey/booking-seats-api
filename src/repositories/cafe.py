from models.cafe import Cafe
from repositories.base import CRUDBase


class CRUDCafe(CRUDBase[Cafe]):
    """CRUD для кафе."""

    pass


cafe_crud = CRUDCafe(Cafe)
