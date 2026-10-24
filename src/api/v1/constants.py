"""Константы для работы с медиафайлами: директория, лимиты, допустимые типы."""

from pathlib import Path

MEDIA_DIR = Path('media')
MEDIA_DIR.mkdir(exist_ok=True)

MAX_FILE_SIZE = 5 * 1024 * 1024
ALLOWED_CONTENT_TYPES = frozenset({'image/jpeg', 'image/png'})
