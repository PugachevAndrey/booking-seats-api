"""Правила валидации бизнес-данных."""

from datetime import date, time

from fastapi.exceptions import RequestValidationError

from shared.core.errors import ValidationError

VALIDATION_ERROR_CODE = 'VALIDATION_ERROR'
DEFAULT_VALIDATION_MESSAGE = 'Некорректные данные.'
DEFAULT_HTTP_MESSAGE = 'Ошибка запроса.'

MEDIA_FILE_NAME_MAX_LENGTH = 50
BOOKING_NOTE_MAX_LENGTH = 255


def ensure_text_not_blank(value: str, field_title: str) -> None:
    """Проверяет, что строка не пустая и не из одних пробелов."""
    if not value or not value.strip():
        raise ValidationError(f'{field_title} не может быть пустым.')


def ensure_max_length(
    value: str,
    field_title: str,
    max_length: int,
) -> None:
    """Проверяет максимальную длину строки."""
    if len(value) > max_length:
        raise ValidationError(
            f'{field_title} не должно быть длиннее {max_length} символов.',
        )


def validate_media_file_name(file_name: str) -> None:
    """Проверяет имя медиафайла.

    В схеме MediaInfo имени файла нет, схема эту проверку не заменяет.
    """
    ensure_text_not_blank(file_name, 'Имя файла')
    ensure_max_length(
        file_name,
        'Имя файла',
        MEDIA_FILE_NAME_MAX_LENGTH,
    )


def validate_slot_time_range(start_time: time, end_time: time) -> None:
    """Проверяет, что время завершения позже времени начала.

    Межполевая проверка: вызывается из схемы TimeSlotCreate
    и из сервиса при частичном обновлении слота.
    """
    if end_time <= start_time:
        raise ValidationError(
            'Время завершения должно быть позже времени начала.',
        )


def validate_booking_date(booking_date: date) -> None:
    """Проверяет, что дата бронирования не в прошлом.

    Схема не может сравнить дату с текущей — это делает только сервис.
    """
    if booking_date < date.today():
        raise ValidationError(
            'Дата бронирования не может быть в прошлом.',
        )


def validate_booking_note(note: str | None) -> None:
    """Проверяет длину заметки к бронированию."""
    if note is None:
        return
    ensure_max_length(note, 'Заметка', BOOKING_NOTE_MAX_LENGTH)


def build_validation_message(
    exception: RequestValidationError,
) -> str:
    """Собирает читаемое сообщение об ошибке валидации.

    Пример результата: "body.email: Field required".
    """
    validation_errors = exception.errors()
    if not validation_errors:
        return DEFAULT_VALIDATION_MESSAGE

    first_error = validation_errors[0]
    location = '.'.join(str(part) for part in first_error.get('loc', ()))
    reason = first_error.get('msg', '')

    if location and reason:
        return f'{location}: {reason}'
    return reason or location or DEFAULT_VALIDATION_MESSAGE


def build_validation_error_content(
    exception: RequestValidationError,
) -> dict[str, str]:
    """Возвращает тело ответа для ошибки валидации."""
    return {
        'code': VALIDATION_ERROR_CODE,
        'message': build_validation_message(exception),
    }


def build_http_error_code(status_code: int) -> str:
    """Формирует код ошибки: 422 -> VALIDATION_ERROR, 401 -> HTTP_401."""
    if status_code == 422:
        return VALIDATION_ERROR_CODE
    return f'HTTP_{status_code}'
