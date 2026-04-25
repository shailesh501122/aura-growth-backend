"""
Custom exceptions and FastAPI exception handlers for centralized error handling.
"""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse


# ── Custom Exceptions ────────────────────────────────────────────────────

class AppException(Exception):
    """Base application exception."""

    def __init__(self, detail: str, status_code: int = 400):
        self.detail = detail
        self.status_code = status_code
        super().__init__(detail)


class NotFoundError(AppException):
    def __init__(self, resource: str = "Resource"):
        super().__init__(
            detail=f"{resource} not found",
            status_code=status.HTTP_404_NOT_FOUND,
        )


class UnauthorizedError(AppException):
    def __init__(self, detail: str = "Invalid credentials"):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_401_UNAUTHORIZED,
        )


class ForbiddenError(AppException):
    def __init__(self, detail: str = "Insufficient permissions"):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_403_FORBIDDEN,
        )


class ConflictError(AppException):
    def __init__(self, detail: str = "Resource already exists"):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_409_CONFLICT,
        )


class RateLimitError(AppException):
    def __init__(self, detail: str = "Rate limit exceeded"):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        )


class BadRequestError(AppException):
    def __init__(self, detail: str = "Bad request"):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_400_BAD_REQUEST,
        )


class UsageLimitError(AppException):
    def __init__(self, detail: str = "Usage limit exceeded for your plan"):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_403_FORBIDDEN,
        )


# ── Exception Handlers ──────────────────────────────────────────────────

def register_exception_handlers(app: FastAPI) -> None:
    """Register all custom exception handlers on the FastAPI app."""

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": exc.detail,
            },
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": "An unexpected error occurred",
            },
        )
