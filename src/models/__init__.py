"""Пакет моделей базы данных приложения."""

from src.models.booking import Booking
from src.models.booking_tables_slot import BookingTablesSlot
from src.models.cafe import Cafe
from src.models.slot import Slot
from src.models.user import User

__all__ = (
    'User',
    'Booking',
    'Cafe',
    'BookingTablesSlot',
    'Slot',
)
