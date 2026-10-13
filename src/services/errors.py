from typing import Any


class DomainError(Exception):
    """Базовое доменное исключение."""

    default_message = 'Доменная ошибка.'
    status_code = 400

    def __init__(self, message: str | None = None) -> None:
        """Создаёт исключение с сообщением или значением по умолчанию."""
        self.message = message or self.default_message
        super().__init__(self.message)


class NotFoundError(DomainError):
    """Объект не найден."""

    default_message = 'Объект не найден.'
    status_code = 404


class ConflictError(DomainError):
    """Конфликт данных."""

    default_message = 'Конфликт данных.'
    status_code = 409


class ValidationError(DomainError):
    """Ошибка валидации на уровне домена."""

    default_message = 'Некорректные данные.'
    status_code = 422


class PermissionDeniedError(DomainError):
    """Недостаточно прав."""

    default_message = 'Недостаточно прав.'
    status_code = 403


def error_payload(error: DomainError) -> dict[str, Any]:
    """Сериализует доменную ошибку в словарь ответа."""
    return {
        'detail': error.message,
        'type': type(error).__name__,
        'status_code': error.status_code,
    }
