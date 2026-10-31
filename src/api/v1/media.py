"""Роутер медиафайлов: загрузка и получение изображений."""

import io
import uuid
from pathlib import Path
from typing import Annotated

from PIL import Image, UnidentifiedImageError
from fastapi import APIRouter, Depends, File, UploadFile, status
from fastapi.responses import FileResponse

from api.v1.constants import (
    ALLOWED_CONTENT_TYPES,
    MAX_FILE_SIZE,
    MEDIA_DIR,
    UPLOAD_CHUNK_SIZE,
)
from api.v1.deps import DbSession, get_current_staff
from schemas.media import MediaInfo
from services.media import create_media, get_media
from shared.core.errors import NotFoundError, ValidationError
from shared.models.user import User

router = APIRouter(prefix='/media', tags=['Медиа'])


def _media_path(media_id: uuid.UUID) -> Path:
    return MEDIA_DIR / f'{media_id}.jpg'


async def _read_limited(file: UploadFile, max_size: int) -> bytes:
    """Читает файл частями, не держа в памяти больше max_size байт.

    Чтение прерывается сразу после превышения лимита.
    """
    chunks: list[bytes] = []
    total = 0
    while chunk := await file.read(UPLOAD_CHUNK_SIZE):
        total += len(chunk)
        if total > max_size:
            raise ValidationError('Файл больше 5 Мб.')
        chunks.append(chunk)
    return b''.join(chunks)


@router.post(
    '',
    response_model=MediaInfo,
    status_code=status.HTTP_201_CREATED,
    summary='Загрузка изображения',
)
async def upload_media(
    file: Annotated[UploadFile, File(...)],
    session: DbSession,
    current_user: Annotated[User, Depends(get_current_staff)],
) -> MediaInfo:
    """Загрузка JPG/PNG."""
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise ValidationError('Поддерживаются только JPG и PNG.')

    content = await _read_limited(file, MAX_FILE_SIZE)

    try:
        image = Image.open(io.BytesIO(content))
        image.load()
    except UnidentifiedImageError:
        raise ValidationError('Не удалось прочитать изображение.')

    if image.mode != 'RGB':
        image = image.convert('RGB')

    media = await create_media(
        session=session,
        actor_role=current_user.role,
        file_name=file.filename or 'image.jpg',
    )

    buffer = io.BytesIO()
    image.save(buffer, format='JPEG', quality=90)
    _media_path(media.id).write_bytes(buffer.getvalue())
    await session.commit()

    return MediaInfo(media_id=media.id)


@router.get(
    '/{media_id}',
    summary='Возвращает изображение в бинарном формате',
)
async def download_media(
    media_id: uuid.UUID,
    session: DbSession,
) -> FileResponse:
    """Отдаёт файл по частям."""
    await get_media(session, media_id)

    path = _media_path(media_id)
    if not path.exists():
        raise NotFoundError(f'Медиафайл {media_id} не найден.')

    return FileResponse(path, media_type='image/jpeg')
