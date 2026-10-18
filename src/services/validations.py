from datetime import date, time

from fastapi.exceptions import RequestValidationError

from .errors import ValidationError

VALIDATION_ERROR_CODE = 'VALIDATION_ERROR'
DEFAULT_VALIDATION_MESSAGE = 'Некорректные данные.'
DEFAULT_HTTP_MESSAGE = 'Ошибка запроса.'

MEDIA_FILE_NAME_MAX_LENGTH = 50
CAFE_NAME_MAX_LENGTH = 255
CAFE_ADDRESS_MAX_LENGTH = 500
CAFE_PHONE_MAX_LENGTH = 20
DESCRIPTION_MAX_LENGTH = 255
BOOKING_NOTE_MAX_LENGTH = 255
USERNAME_MAX_LENGTH = 100
EMAIL_MAX_LENGTH = 255
USER_PHONE_MAX_LENGTH = 20
TG_ID_MAX_LENGTH = 50
PASSWORD_MIN_LENGTH = 8


def ensure_positive_number(value: int, field_title: str) -> None:
    """Проверяет, что число больше нуля."""
    if value <= 0:
        raise ValidationError(
            f'{field_title} должно быть больше нуля.',
        )


def ensure_text_not_blank(value: str, field_title: str) -> None:
    """Проверяет, что строка не пустая и не из одних пробелов."""
    if not value or not value.strip():
        raise ValidationError(
            f'{field_title} не может быть пустым.',
        )


def ensure_max_length(
    value: str,
    field_title: str,
    max_length: int,
) -> None:
    """Проверяет максимальную длину строки."""
    if len(value) > max_length:
        raise ValidationError(
            f'{field_title} не должно быть длиннее '
            f'{max_length} символов.',
        )


def validate_user_password(password: str) -> None:
    """Проверяет минимальные требования к паролю."""
    ensure_text_not_blank(password, 'Пароль')
    if len(password) < PASSWORD_MIN_LENGTH:
        raise ValidationError(
            'Пароль должен содержать не менее '
            f'{PASSWORD_MIN_LENGTH} символов.',
        )


def validate_role(role: str, allowed_roles: tuple[str, ...]) -> None:
    """Проверяет, что роль входит в допустимый набор."""
    if role not in allowed_roles:
        allowed_text = ', '.join(allowed_roles)
        raise ValidationError(
            f'Недопустимая роль. Разрешены: {allowed_text}.',
        )


def validate_role_change(
    actor_id: int,
    user_id: int,
    actor_role: str,
    admin_role: str,
) -> None:
    """Проверяет право менять роль пользователя."""
    if actor_id == user_id:
        raise ValidationError('Нельзя менять собственную роль.')
    if actor_role != admin_role:
        raise ValidationError(
            'Только администратор может менять роль.',
        )


def validate_cafe_name(name: str) -> None:
    """Проверяет название кафе."""
    ensure_text_not_blank(name, 'Название кафе')
    ensure_max_length(name, 'Название кафе', CAFE_NAME_MAX_LENGTH)


def validate_cafe_address(address: str) -> None:
    """Проверяет адрес кафе."""
    ensure_text_not_blank(address, 'Адрес кафе')
    ensure_max_length(address, 'Адрес кафе', CAFE_ADDRESS_MAX_LENGTH)


def validate_cafe_phone(phone: str) -> None:
    """Проверяет формат телефона кафе."""
    ensure_text_not_blank(phone, 'Телефон')
    ensure_max_length(phone, 'Телефон', CAFE_PHONE_MAX_LENGTH)
    digits = sum(character.isdigit() for character in phone)
    if digits < 10:
        raise ValidationError(
            'Телефон должен содержать не менее 10 цифр.',
        )


def validate_cafe_fields(
    name: str,
    address: str,
    phone: str,
) -> None:
    """Проверяет название, адрес и телефон кафе."""
    validate_cafe_name(name)
    validate_cafe_address(address)
    validate_cafe_phone(phone)


def validate_cafe_description(description: str | None) -> None:
    """Проверяет описание кафе, если оно задано."""
    if not description:
        return
    ensure_text_not_blank(description, 'Описание кафе')
    ensure_max_length(description, 'Описание кафе', DESCRIPTION_MAX_LENGTH)


def validate_media_file_name(file_name: str) -> None:
    """Проверяет имя медиафайла."""
    ensure_text_not_blank(file_name, 'Имя файла')
    ensure_max_length(
        file_name,
        'Имя файла',
        MEDIA_FILE_NAME_MAX_LENGTH,
    )


def validate_slot_description(description: str | None) -> None:
    """Проверяет описание слота, если оно задано."""
    if not description:
        return
    ensure_text_not_blank(description, 'Описание слота')
    ensure_max_length(description, 'Описание слота', DESCRIPTION_MAX_LENGTH)


def validate_table_description(description: str | None) -> None:
    """Проверяет описание стола, если оно задано."""
    if not description:
        return
    ensure_text_not_blank(description, 'Описание стола')
    ensure_max_length(description, 'Описание стола', DESCRIPTION_MAX_LENGTH)


def validate_slot_time_range(start_time: time, end_time: time) -> None:
    """Проверяет, что время завершения позже времени начала."""
    if end_time <= start_time:
        raise ValidationError(
            'Время завершения должно быть позже времени начала.',
        )


def validate_table_seat_number(seat_number: int) -> None:
    """Проверяет количество мест за столом."""
    ensure_positive_number(seat_number, 'Количество мест')


def validate_booking_date(booking_date: date) -> None:
    """Проверяет, что дата бронирования не в прошлом."""
    if booking_date < date.today():
        raise ValidationError(
            'Дата бронирования не может быть в прошлом.',
        )


def validate_booking_guest_number(guest_number: int) -> None:
    """Проверяет количество гостей."""
    ensure_positive_number(guest_number, 'Количество гостей')


def validate_booking_note(note: str | None) -> None:
    """Проверяет длину заметки к бронированию."""
    if note is None:
        return
    ensure_max_length(note, 'Заметка', BOOKING_NOTE_MAX_LENGTH)


def validate_booking_status(
    status: str,
    allowed_statuses: tuple[str, ...],
) -> None:
    """Проверяет, что статус бронирования допустим."""
    if status not in allowed_statuses:
        allowed_text = ', '.join(allowed_statuses)
        raise ValidationError(
            f'Недопустимый статус. Разрешены: {allowed_text}.',
        )


def validate_user_fields(
    username: str,
    email: str | None,
    phone: str | None,
    tg_id: str | None,
) -> None:
    """Проверяет поля пользователя, которые переданы.

    `username` обязателен. Поля `email`, `phone`, `tg_id` проверяются,
    только если они не `None`. Требование «email или phone» и запрет
    обоих пустыми — в схеме (`UserCreate.check_login`) и в сервисе
    (`create_user`), здесь не дублируются.
    """
    ensure_text_not_blank(username, 'Имя пользователя')
    ensure_max_length(username, 'Имя пользователя', USERNAME_MAX_LENGTH)
    if email is not None:
        ensure_text_not_blank(email, 'Эл. почта')
        ensure_max_length(email, 'Эл. почта', EMAIL_MAX_LENGTH)
    if phone is not None:
        ensure_text_not_blank(phone, 'Телефон')
        ensure_max_length(phone, 'Телефон', USER_PHONE_MAX_LENGTH)
    if tg_id is not None:
        ensure_text_not_blank(tg_id, 'ID Телеграмма')
        ensure_max_length(tg_id, 'ID Телеграмма', TG_ID_MAX_LENGTH)


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
    location_parts = first_error.get('loc', ())
    location = '.'.join(str(part) for part in location_parts)
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
