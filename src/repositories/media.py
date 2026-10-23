from models.media import Media
from repositories.base import CRUDBase


class CRUDMedia(CRUDBase[Media]):
    """CRUD для медиа.

    Метод update не поддерживается по матрице прав
    (для медиа доступны только Crec и Rrec).
    """


media_crud = CRUDMedia(Media)
