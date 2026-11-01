"""Перечисления (enum) для проекта."""

from enum import Enum


class UserRole(str, Enum):
    """Роль пользователя."""

    ADMIN = 'ADMIN'
    MANAGER = 'MANAGER'
    USER = 'USER'


class BookingStatus(str, Enum):
    """Статус бронирования."""

    BOOKING = 'BOOKING'
    CANCELED = 'CANCELED'
    COMPLETED = 'COMPLETED'
    ACTIVE = 'ACTIVE'
