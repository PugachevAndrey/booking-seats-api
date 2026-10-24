"""Пакет моделей базы данных приложения."""

from shared.models.booking import Booking
from shared.models.booking_tables_slot import BookingTablesSlot
from shared.models.cafe import Cafe
from shared.models.cafe_manager import CafeManager
from shared.models.media import Media
from shared.models.slot import Slot
from shared.models.table import Table
from shared.models.user import User

__all__ = (
    'User',
    'Booking',
    'Cafe',
    'BookingTablesSlot',
    'Slot',
    'Table',
    'Media',
    'CafeManager',
)
