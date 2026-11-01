"""Бизнес-логика медиафайлов."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from repositories.media import media_crud
from shared.core.errors import NotFoundError
from shared.models.media import Media
from validators import validate_media_file_name

from .access import ensure_staff


async def get_media(
    session: AsyncSession,
    media_id: uuid.UUID,
) -> Media:
    """Возвращает медиафайл по ID."""
    media = await media_crud.get(session=session, obj_id=media_id)
    if media is None:
        raise NotFoundError(f'Медиафайл {media_id} не найден.')
    return media


async def create_media(
    session: AsyncSession,
    actor_role: str,
    file_name: str,
) -> Media:
    """Создаёт запись метаданных медиафайла.

    Содержимое, MIME и размер проверяются в роутере (api/v1/media.py)
    до вызова сервиса.

    Коммит не выполняется: запись фиксирует вызывающий код
    (роутер) после успешной записи файла на диск, чтобы в БД
    не оставались записи без файла.
    """
    ensure_staff(actor_role)
    validate_media_file_name(file_name)

    return await media_crud.create_from_dict(
        session=session,
        data={'file_name': file_name},
    )
