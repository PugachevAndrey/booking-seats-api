from crud.base import CRUDBase
from models.cafe import Cafe


class CRUDCafe(CRUDBase[Cafe]):
    pass


cafe_crud = CRUDCafe(Cafe)
