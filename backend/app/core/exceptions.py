# api/core/exceptions.py
from fastapi import HTTPException, Request, status
from fastapi.exceptions import RequestValidationError

from .response import ApiJSONResponse


async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTPException and return unified error response."""
    return ApiJSONResponse(
        status_code=exc.status_code,
        content={
            "data": None,
            "error": exc.detail
        }
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors and return unified error response."""
    # Extract validation error details
    errors = exc.errors()
    error_messages = []
    for error in errors:
        loc = " -> ".join(str(l) for l in error["loc"])
        msg = f"{loc}: {error['msg']}"
        error_messages.append(msg)

    return ApiJSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "data": None,
            "error": "; ".join(error_messages)
        }
    )


async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors and return unified error response."""
    # Log the actual error here if you have logging configured
    # logger.error(f"Unexpected error: {exc}", exc_info=True)

    return ApiJSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "data": None,
            "error": "Internal server error"
        }
    )
