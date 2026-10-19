import uuid

from fastapi import APIRouter, File, UploadFile, status

from schemas.media import MediaInfo

router = APIRouter(prefix='/media', tags=['Медиа'])


@router.post('', response_model=MediaInfo, status_code=status.HTTP_201_CREATED)
async def upload_media(file: UploadFile = File(...)) -> MediaInfo:
    """Загрузка катинки."""
    return MediaInfo(media_id=uuid.uuid4())


@router.get('/{media_id}')
async def get_media(media_id: uuid.UUID) -> dict:
    """Возвращает картинку."""
    return {'detail': 'Картинка'}
