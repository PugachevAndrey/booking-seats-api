import uuid

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from models.media import Media
from repositories.cafe import cafe_crud
from repositories.media import media_crud
from validators import validate_media_file_name

from .access import ensure_staff, is_admin
from core.errors import (
    ConflictError,
    NotFoundError,
    PermissionDeniedError,
)


class _MediaCreate(BaseModel):
    """Внутренняя схема создания записи медиа."""

    file_name: str


async def get_media(
    session: AsyncSession,
    media_id: uuid.UUID,
) -> Media:
    """Возвращает медиафайл по ID."""
    media = await media_crud.get(session=session, obj_id=media_id)
    if media is None:
        raise NotFoundError(f'Медиафайл {media_id} не найден.')
    return media


async def _get_owner_cafe_id(
    session: AsyncSession,
    media_id: uuid.UUID,
) -> int | None:
    """Возвращает ID кафе, использующего медиа (или None)."""
    cafes = await cafe_crud.get_multi(session=session)
    for cafe in cafes:
        if cafe.is_active and cafe.photo_id == media_id:
            return cafe.id
    return None


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

    return await media_crud.create(
        session=session,
        obj_in=_MediaCreate(file_name=file_name),
    )


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
        session,
        actor_role,
        actor_cafe_id,
        media_id,
    )

    owner_cafe_id = await _get_owner_cafe_id(session, media_id)
    if owner_cafe_id is not None:
        raise ConflictError(
            f'Медиафайл используется кафе {owner_cafe_id}. Сначала отвяжите его.',
        )

    await media_crud.remove(session=session, db_obj=media)
