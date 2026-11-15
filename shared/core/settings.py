"""Конфигурация приложения через pydantic-settings."""

import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Настройки приложения."""

    # Общие настройки
    title: str = 'Система бронирования мест в кафе'
    version: str = '1.0.0'
    description: str = 'API для управления '
    'бронированием столов и предзаказом меню'

    # Настройки подключения к БД
    postgres_user: str
    postgres_password: str
    postgres_db: str
    postgres_server: str = 'localhost'
    postgres_port: int = 5432

    # Настройки RabbitMQ
    rabbitmq_user: str = 'guest'
    rabbitmq_password: str = 'guest'
    rabbitmq_host: str = 'rabbitmq'
    rabbitmq_port: int = 5672

    # Настройки SMS
    sms_api_key: str = ''
    sms_sender: str = ''

    # Настройки SMTP
    smtp_host: str = ''
    smtp_port: int = 587
    smtp_user: str = ''
    smtp_password: str = ''
    smtp_from: str = ''
    smtp_use_ssl: bool = True

    # Настройки Telegram
    telegram_bot_token: str = ''

    # Настройки JWT
    secret_key: str
    algorithm: str = 'HS256'
    access_token_expire_minutes: int = 60 * 24

    model_config = SettingsConfigDict(
        env_file=os.getenv('ENV_FILE', str(BASE_DIR / '../infra/.env')),
        env_file_encoding='utf-8',
        extra='ignore',
    )

    @property
    def db_url(self) -> str:
        """Строка подключения к БД."""
        return (
            f'postgresql+asyncpg://{
                self.postgres_user
            }:{self.postgres_password}@'
            f'{self.postgres_server}:{self.postgres_port}/{self.postgres_db}'
        )

    @property
    def rabbitmq_url(self) -> str:
        """URL для подключения к RabbitMQ."""
        return (
            f'amqp://{self.rabbitmq_user}:{self.rabbitmq_password}'
            f'@{self.rabbitmq_host}:{self.rabbitmq_port}//'
        )


settings = Settings()
