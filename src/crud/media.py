from crud.base import CRUDBase
from models.media import Media


class CRUDMedia(CRUDBase[Media]):
    """Урезанный CRUD — по матрице прав доступны только Crec и Rrec.

    Методы update и soft_delete намеренно не добавлены,
    чтобы их случайно не вызвали из API.
    """

    pass


media_crud = CRUDMedia(Media)
