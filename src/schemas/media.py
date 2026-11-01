"""Схемы медиафайлов."""

from uuid import UUID

from schemas.base import BaseSchema


class MediaInfo(BaseSchema):
    """Схема инфо media_id."""

    media_id: UUID
