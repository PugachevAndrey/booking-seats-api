from contextlib import asynccontextmanager
from typing import AsyncGenerator

import uvicorn
from fastapi import FastAPI

from services.exception_handlers import register_exception_handlers

from core.settings import settings


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
