"""Константы ограничений для полей схем."""

from typing import Annotated

from pydantic import BeforeValidator
from pydantic_extra_types.phone_numbers import PhoneNumber

MAX_LENGTH = 255
MAX_USERNAME_LENGTH = 100
MAX_TG_LENGTH = 50
MIN_LENGTH = 20
ADDRESS_LENGTH = 500
MIN_SYMBOL = 1

MIN_PASS = 8


def _require_plus_prefix(v: str) -> str:
    """Проверяет, что номер начинается с плюса до основной валидации."""
    if isinstance(v, str) and not v.startswith('+'):
        raise ValueError(
            'Номер телефона должен начинаться с + (например, +79991234567)',
        )
    return v


StrictPhoneNumber = Annotated[PhoneNumber, BeforeValidator(
    _require_plus_prefix,
)]
