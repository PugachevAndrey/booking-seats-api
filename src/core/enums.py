"""Перечисления (enum) для проекта."""
from enum import Enum


class UserRole(str, Enum):
    """Роль пользователя."""

    ADMIN = "admin"
    MANAGER = "manager"
    USER = "user"


class BookingStatus(str, Enum):
    """Статус бронирования."""

    BOOKING = "booking"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
