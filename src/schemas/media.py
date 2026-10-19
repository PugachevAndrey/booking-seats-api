from uuid import UUID

from src.schemas.base import BaseSchema


class MediaInfo(BaseSchema):
    """Схема инфо media_id."""

    media_id: UUID
