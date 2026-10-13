from models.media import Media
from repositories.base import CRUDBase


class CRUDMedia(CRUDBase[Media]):
    """Урезанный CRUD: по матрице прав доступны только Crec и Rrec."""

    pass


media_crud = CRUDMedia(Media)
