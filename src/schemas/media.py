from uuid import UUID

from pydantic import BaseModel


class MediaInfo(BaseModel):
    """Схема инфо media_id."""

    media_id: UUID
