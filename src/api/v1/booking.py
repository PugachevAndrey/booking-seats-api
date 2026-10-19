from datetime import date, datetime, timezone

from fastapi import APIRouter, status

from schemas.booking import BookingCreate, BookingInfo, BookingUpdate

from core.enums import BookingStatus

router = APIRouter(prefix='/booking', tags=['Бронирования'])


def fake_booking(id: int = 1) -> dict:  # noqa: A002
    """Временная функция для информации о бронировании для заглушек."""
    return {
        'id': id,
        'user': {'id': 1, 'username': 'username'},
        'cafe': {'id': 1, 'name': 'Кафе 1'},
        'tables_slots': [],
        'guest_number': 2,
        'note': 'Столик у окна',
        'status': BookingStatus.BOOKING,
        'booking_date': date.today(),
        'is_active': True,
        'created_at': datetime.now(timezone.utc),
        'updated_at': datetime.now(timezone.utc),
    }


@router.get('', response_model=list[BookingInfo])
async def get_bookings() -> list:
    """Возвращает список всех бронирований."""
    return [fake_booking(1), fake_booking(2)]


@router.post('', response_model=BookingInfo, status_code=status.HTTP_201_CREATED)
async def create_booking(data: BookingCreate) -> dict:
    """Создание бронирования."""
    return fake_booking(3)


@router.get('/{booking_id}', response_model=BookingInfo)
async def get_booking(booking_id: int) -> dict:
    """Информация о бронировании."""
    return fake_booking(booking_id)


@router.patch('/{booking_id}', response_model=BookingInfo)
async def update_booking(booking_id: int, data: BookingUpdate) -> dict:
    """Обновить информацию о бронировании."""
    return fake_booking(booking_id)
