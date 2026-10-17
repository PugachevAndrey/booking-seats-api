from datetime import datetime, timezone

from fastapi import APIRouter, status

from schemas.table import TableCreate, TableInfo, TableUpdate

router = APIRouter(prefix='/cafes/{cafe_id}/tables', tags=['Столы'])


def fake_table(id: int, cafe_id: int) -> dict:  # noqa: A002
    """Временная функция для информации о столике для заглушек."""
    return {
        'id': id,
        'cafe': {'id': cafe_id, 'name': f'Кафе {cafe_id}'},
        'description': 'У окна',
        'seat_number': 4,
        'is_active': True,
        'created_at': datetime.now(timezone.utc),
        'updated_at': datetime.now(timezone.utc),
    }


@router.get('', response_model=list[TableInfo])
async def get_tables(cafe_id: int) -> list:
    """Список столиков."""
    return [fake_table(1, cafe_id), fake_table(2, cafe_id)]


@router.post('', response_model=TableInfo, status_code=status.HTTP_201_CREATED)
async def create_table(cafe_id: int, data: TableCreate) -> dict:
    """Создание столика."""
    return fake_table(3, cafe_id)


@router.get('/{table_id}', response_model=TableInfo)
async def get_table(cafe_id: int, table_id: int) -> dict:
    """Информация о столике."""
    return fake_table(table_id, cafe_id)


@router.patch('/{table_id}', response_model=TableInfo)
async def update_table(cafe_id: int, table_id: int, data: TableUpdate) -> dict:
    """Обновление информации о столике."""
    return fake_table(table_id, cafe_id)
