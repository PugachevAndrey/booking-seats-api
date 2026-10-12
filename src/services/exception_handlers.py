from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .errors import DomainError, error_payload


def register_exception_handlers(app: FastAPI) -> None:
    """Регистрирует обработчики доменных исключений."""

    @app.exception_handler(DomainError)
    async def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
        """Преобразует доменную ошибку в HTTP-ответ."""
        return JSONResponse(
            status_code=exc.status_code,
            content=error_payload(exc),
        )
