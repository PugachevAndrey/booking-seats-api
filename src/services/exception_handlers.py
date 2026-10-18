import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from validators import (
    DEFAULT_HTTP_MESSAGE,
    build_http_error_code,
    build_validation_error_content,
)

from core.errors import DomainError, error_payload

logger = logging.getLogger(__name__)


def register_exception_handlers(application: FastAPI) -> None:
    """Регистрирует обработчики исключений."""

    @application.exception_handler(DomainError)
    async def handle_domain_error(
        exception: DomainError,
    ) -> JSONResponse:
        """Обрабатывает доменные ошибки приложения."""
        return JSONResponse(
            status_code=exception.status_code,
            content=error_payload(exception),
        )

    @application.exception_handler(RequestValidationError)
    async def handle_validation_error(
        exception: RequestValidationError,
    ) -> JSONResponse:
        """Обрабатывает ошибки валидации запроса."""
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=build_validation_error_content(exception),
        )

    @application.exception_handler(StarletteHTTPException)
    async def handle_http_exception(
        exception: StarletteHTTPException,
    ) -> JSONResponse:
        """Обрабатывает прочие ошибки HTTP."""
        detail = exception.detail
        if isinstance(detail, str):
            message = detail
        elif detail is None:
            message = DEFAULT_HTTP_MESSAGE
        else:
            message = str(detail)
        return JSONResponse(
            status_code=exception.status_code,
            content={
                'code': build_http_error_code(exception.status_code),
                'message': message,
            },
            headers=getattr(exception, 'headers', None) or {},
        )

    @application.exception_handler(Exception)
    async def handle_unexpected_error(
        request: Request,
        exception: Exception,
    ) -> JSONResponse:
        """Отдаёт единый формат для непредвиденных ошибок."""
        logger.exception('Необработанная ошибка', exc_info=exception)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                'code': 'HTTP_500',
                'message': 'Внутренняя ошибка сервера.',
            },
        )
