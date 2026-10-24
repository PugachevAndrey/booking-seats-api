"""Доменные исключения приложения."""

from typing import Any


class DomainError(Exception):
    """Базовое доменное исключение."""

    default_message = 'Доменная ошибка.'
    code = 'DOMAIN_ERROR'
    status_code = 400

    def __init__(self, message: str | None = None) -> None:
        """Создаёт исключение с сообщением или значением по умолчанию."""
        self.message = message or self.default_message
        super().__init__(self.message)


class NotFoundError(DomainError):
    """Объект не найден."""

    default_message = 'Объект не найден.'
    code = 'NOT_FOUND'
    status_code = 404


class ConflictError(DomainError):
    """Конфликт данных."""

    default_message = 'Конфликт данных.'
    code = 'CONFLICT'
    status_code = 409


class ValidationError(DomainError):
    """Ошибка валидации на уровне домена."""

    default_message = 'Некорректные данные.'
    code = 'VALIDATION_ERROR'
    status_code = 422


class PermissionDeniedError(DomainError):
    """Недостаточно прав."""

    default_message = 'Недостаточно прав.'
    code = 'PERMISSION_DENIED'
    status_code = 403


class UnauthorizedError(DomainError):
    """Требуется авторизация или неверные учетные данные."""

    default_message = 'Требуется авторизация.'
    code = 'UNAUTHORIZED'
    status_code = 401


def error_payload(error: DomainError) -> dict[str, Any]:
    """Сериализует доменную ошибку в словарь ответа."""
    return {
        'code': error.code,
        'message': error.message,
    }
