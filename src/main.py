"""Точка входа: сборка FastAPI-приложения и подключение роутеров."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

import uvicorn
from fastapi import FastAPI

from api.v1 import (
    auth,
    booking,
    cafes,
    media,
    slots,
    tables,
    users,
)
from services.exception_handlers import register_exception_handlers
from shared.core.settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Жизненный цикл приложения FastAPI."""
    yield


app = FastAPI(
    title=settings.title,
    version=settings.version,
    description=settings.description,
    lifespan=lifespan,
)

register_exception_handlers(app)

app.include_router(auth.router, prefix='/api/v1')
app.include_router(users.router, prefix='/api/v1')
app.include_router(cafes.router, prefix='/api/v1')
app.include_router(tables.router, prefix='/api/v1')
app.include_router(slots.router, prefix='/api/v1')
app.include_router(booking.router, prefix='/api/v1')
app.include_router(media.router, prefix='/api/v1')


@app.get(
    path='/',
    response_model=dict,
)
async def index() -> dict:
    """Основная страница."""
    return {
        'app': f'{settings.title} ({settings.version})',
        'description': settings.description,
        'status': 'OK',
    }


if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000)
