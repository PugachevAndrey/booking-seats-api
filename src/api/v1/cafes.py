from datetime import datetime, timezone

from fastapi import APIRouter, status

from schemas.cafe import CafeCreate, CafeInfo, CafeUpdate

router = APIRouter(prefix='/cafes', tags=['Кафе'])


def fake_cafe(id: int = 1) -> dict:  # noqa: A002
    """Временная функция для информации о кафе для заглушек."""
    return {
        'id': id,
        'name': f'Кафе {id}',
        'address': 'ул. Пушкина, дом Колотушкина',
        'phone': '+78005553535',
        'description': 'Хорошее кафе',
        'photo_id': None,
        'managers': [],
        'is_active': True,
        'created_at': datetime.now(timezone.utc),
        'updated_at': datetime.now(timezone.utc),
    }


@router.get('', response_model=list[CafeInfo])
async def get_cafes() -> list:
    """Список всех кафе."""
    return [fake_cafe(1), fake_cafe(2)]


@router.post('', response_model=CafeInfo, status_code=status.HTTP_201_CREATED)
async def create_cafe(data: CafeCreate) -> dict:
    """Создание кафе."""
    return fake_cafe(3)


@router.get('/{cafe_id}', response_model=CafeInfo)
async def get_cafe(cafe_id: int) -> dict:
    """Информация о кафе."""
    return fake_cafe(cafe_id)


@router.patch('/{cafe_id}', response_model=CafeInfo)
async def update_cafe(cafe_id: int, data: CafeUpdate) -> dict:
    """Обновление кафе."""
    return fake_cafe(cafe_id)
