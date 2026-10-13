import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.media import Media

from .access import ensure_staff
from .errors import NotFoundError


async def get_media(session: AsyncSession, media_id: uuid.UUID) -> Media:
    """Возвращает медиафайл по ID."""
    media = await session.get(Media, media_id)
    if media is None:
        raise NotFoundError(f'Медиафайл {media_id} не найден.')
    return media


async def get_media_list(session: AsyncSession) -> list[Media]:
    """Возвращает список медиафайлов."""
    result = await session.execute(select(Media).order_by(Media.id))
    return list(result.scalars().all())


async def create_media(
    session: AsyncSession,
    actor_role: str,
    content_type: str,
) -> Media:
    """Создаёт запись метаданных медиафайла."""
    ensure_staff(actor_role)
    media = Media(content_type=content_type)
    session.add(media)
    await session.flush()
    await session.refresh(media)
    return media


async def delete_media(
    session: AsyncSession,
    actor_role: str,
    media_id: uuid.UUID,
) -> None:
    """Удаляет запись о медиафайле."""
    ensure_staff(actor_role)
    media = await get_media(session, media_id)
    await session.delete(media)
    await session.flush()
