from datetime import datetime, timezone

from fastapi import APIRouter, status

from schemas.dish import DishCreate, DishInfo, DishUpdate

router = APIRouter(prefix='/dishes', tags=['Блюда'])


def fake_dish(id: int = 1) -> dict:  # noqa: A002
    """Временная функция для информации о блюде для заглушек."""
    return {
        'id': id,
        'name': 'Суп',
        'description': 'Рыбный',
        'photo_id': None,
        'price': 500.0,
        'cafes': [],
        'is_active': True,
        'created_at': datetime.now(timezone.utc),
        'updated_at': datetime.now(timezone.utc),
    }


@router.get('', response_model=list[DishInfo])
async def get_dishes() -> list:
    """Возвращает список блюд."""
    return [fake_dish(1), fake_dish(2)]


@router.post('', response_model=DishInfo, status_code=status.HTTP_201_CREATED)
async def create_dish(data: DishCreate) -> dict:
    """Создание блюда."""
    return fake_dish(3)


@router.get('/{dish_id}', response_model=DishInfo)
async def get_dish(dish_id: int) -> dict:
    """Информация о блюде."""
    return fake_dish(dish_id)


@router.patch('/{dish_id}', response_model=DishInfo)
async def update_dish(dish_id: int, data: DishUpdate) -> dict:
    """Обновление информации о блюде."""
    return fake_dish(dish_id)
