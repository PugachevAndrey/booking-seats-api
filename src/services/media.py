import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.cafe import Cafe
from models.media import Media

from .access import ensure_staff, is_admin
from .errors import (
    ConflictError,
    NotFoundError,
    PermissionDeniedError,
)
from .validations import validate_media_file_name


async def get_media(
    session: AsyncSession,
    media_id: uuid.UUID,
) -> Media:
    """Возвращает медиафайл по ID."""
    media = await session.get(Media, media_id)
    if media is None:
        raise NotFoundError(f'Медиафайл {media_id} не найден.')
    return media


async def get_media_list(session: AsyncSession) -> list[Media]:
    """Возвращает список медиафайлов."""
    result = await session.execute(select(Media).order_by(Media.id))
    return list(result.scalars().all())


async def _get_owner_cafe_id(
    session: AsyncSession,
    media_id: uuid.UUID,
) -> int | None:
    """Возвращает ID кафе, использующего медиа (или None)."""
    result = await session.execute(
        select(Cafe.id)
        .where(Cafe.photo_id == media_id, Cafe.is_active.is_(True))
        .order_by(Cafe.id),
    )
    return result.scalars().first()


async def _ensure_media_access(
    session: AsyncSession,
    actor_role: str,
    actor_cafe_id: int | None,
    media_id: uuid.UUID,
) -> None:
    """Проверяет, что персонал вправе трогать этот медиафайл."""
    if is_admin(actor_role):
        return
    owner_cafe_id = await _get_owner_cafe_id(session, media_id)
    if owner_cafe_id is None:
        raise PermissionDeniedError(
            'Нет прав на работу со свободным медиафайлом.',
        )
    if actor_cafe_id != owner_cafe_id:
        raise PermissionDeniedError(
            'Нет прав на работу с медиафайлом другого кафе.',
        )


async def create_media(
    session: AsyncSession,
    actor_role: str,
    file_name: str,
) -> Media:
    """Создаёт запись метаданных медиафайла."""
    ensure_staff(actor_role)
    validate_media_file_name(file_name)
    media = Media(file_name=file_name)
    session.add(media)
    await session.flush()
    await session.refresh(media)
    return media


async def delete_media(
    session: AsyncSession,
    actor_role: str,
    actor_cafe_id: int | None,
    media_id: uuid.UUID,
) -> None:
    """Удаляет медиафайл с проверкой прав и занятости."""
    ensure_staff(actor_role)
    media = await get_media(session, media_id)
    await _ensure_media_access(
        session, actor_role, actor_cafe_id, media_id,
    )

    owner_cafe_id = await _get_owner_cafe_id(session, media_id)
    if owner_cafe_id is not None:
        raise ConflictError(
            f'Медиафайл используется кафе {owner_cafe_id}. '
            'Сначала отвяжите его.',
        )

    await session.delete(media)
    await session.flush()
