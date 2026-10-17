import uuid

from pydantic import BaseModel


class MediaInfo(BaseModel):
    """Информация о медиа."""

    media_id: uuid.UUID
