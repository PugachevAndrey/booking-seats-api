import io
import uuid
from pathlib import Path
from typing import Annotated

from PIL import Image, UnidentifiedImageError
from fastapi import APIRouter, Depends, File, UploadFile, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.constants import (
    ALLOWED_CONTENT_TYPES,
    MAX_FILE_SIZE,
    MEDIA_DIR,
)
from api.v1.deps import get_current_staff, get_db
from schemas.media import MediaInfo
from services.media import create_media, get_media
from shared.core.errors import NotFoundError, ValidationError
from shared.models.user import User

router = APIRouter(prefix='/media', tags=['Медиа'])


def _media_path(media_id: uuid.UUID) -> Path:
    return MEDIA_DIR / f'{media_id}.jpg'


@router.post(
    '',
    response_model=MediaInfo,
    status_code=status.HTTP_201_CREATED,
    summary='Загрузка изображения',
)
async def upload_media(
    file: Annotated[UploadFile, File(...)],
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_staff)],
) -> MediaInfo:
    """Загрузка JPG/PNG."""
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise ValidationError('Поддерживаются только JPG и PNG.')

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise ValidationError('Файл больше 5 Мб.')

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

    return MediaInfo(media_id=media.id)


@router.get(
    '/{media_id}',
    summary='Возвращает изображение в бинарном формате',
)
async def download_media(
    media_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
    """Отдаёт файл."""
    await get_media(session, media_id)

    path = _media_path(media_id)
    if not path.exists():
        raise NotFoundError(f'Медиафайл {media_id} не найден.')

    return Response(
        content=path.read_bytes(),
        media_type='image/jpeg',
    )
