"""Перечисления (enum) для проекта."""

from enum import Enum


class UserRole(str, Enum):
    """Роль пользователя."""

    ADMIN = 'admin'
    MANAGER = 'manager'
    USER = 'user'


class BookingStatus(str, Enum):
    """Статус бронирования."""

    ACTIVE = 'active'
    BOOKING = 'booking'
    CANCELLED = 'cancelled'
    COMPLETED = 'completed'
