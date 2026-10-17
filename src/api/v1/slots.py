from datetime import datetime, time, timezone

from fastapi import APIRouter, status

from schemas.slot import SlotCreate, SlotInfo, SlotUpdate

router = APIRouter(prefix='/cafes/{cafe_id}/time_slots', tags=['Временные слоты'])


def fake_slot(id: int, cafe_id: int) -> dict:  # noqa: A002
    """Временная функция для информации о слоте для заглушек."""
    return {
        'id': id,
        'cafe': {'id': cafe_id, 'name': f'Кафе {cafe_id}'},
        'start_time': time(10, 0),
        'end_time': time(12, 0),
        'description': 'Утро',
        'is_active': True,
        'created_at': datetime.now(timezone.utc),
        'updated_at': datetime.now(timezone.utc),
    }


@router.get('', response_model=list[SlotInfo])
async def get_slots(cafe_id: int) -> list:
    """Возвращает список слотов."""
    return [fake_slot(1, cafe_id), fake_slot(2, cafe_id)]


@router.post('', response_model=SlotInfo, status_code=status.HTTP_201_CREATED)
async def create_slot(cafe_id: int, data: SlotCreate) -> dict:
    """Создать временной слот."""
    return fake_slot(3, cafe_id)


@router.get('/{slot_id}', response_model=SlotInfo)
async def get_slot(cafe_id: int, slot_id: int) -> dict:
    """Информация о слоте."""
    return fake_slot(slot_id, cafe_id)


@router.patch('/{slot_id}', response_model=SlotInfo)
async def update_slot(cafe_id: int, slot_id: int, data: SlotUpdate) -> dict:
    """Обновить информацию о слоте."""
    return fake_slot(slot_id, cafe_id)
