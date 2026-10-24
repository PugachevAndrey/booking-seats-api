from repositories.base import CRUDBase
from shared.models.media import Media


class CRUDMedia(CRUDBase[Media]):
    """CRUD для медиа.

    Метод update не поддерживается по матрице прав
    (для медиа доступны только Crec и Rrec).
    """


media_crud = CRUDMedia(Media)
