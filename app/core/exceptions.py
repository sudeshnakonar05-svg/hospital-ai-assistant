"""Application-level exceptions and FastAPI handlers."""

from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class AppError(Exception):
    """Domain error mapped to an HTTP response."""

    def __init__(self, status_code: int, detail: str, error_code: str = "app_error") -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail
        self.error_code = error_code


def register_exception_handlers(app: FastAPI) -> None:
    """Attach centralized exception handlers to the FastAPI app."""

    @app.exception_handler(AppError)
    async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail, "error_code": exc.error_code},
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(_request: Request, exc: StarletteHTTPException) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        _request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={"detail": exc.errors(), "error_code": "validation_error"},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
        if isinstance(exc, (AppError, StarletteHTTPException, RequestValidationError)):
            raise exc
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error", "error_code": "internal_error"},
        )


def error_payload(detail: str, error_code: str = "error") -> dict[str, Any]:
    """Build a consistent error body."""
    return {"detail": detail, "error_code": error_code}
