"""Настройка логирования: консоль + файл с ротацией."""

import logging
import os
from logging.handlers import RotatingFileHandler

LOG_DIR = 'logs'
LOG_FILE = os.path.join(LOG_DIR, 'app.log')
MAX_BYTES = 10 * 1024 * 1024  # 10 МБ
BACKUP_COUNT = 5


def setup_logging() -> None:
    """Настраивает root logger: консоль + файл (ротация)."""
    os.makedirs(LOG_DIR, exist_ok=True)

    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)s | %(name)s | %(message)s',
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=MAX_BYTES,
        backupCount=BACKUP_COUNT,
        encoding='utf-8',
    )
    file_handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(console_handler)
    root.addHandler(file_handler)
