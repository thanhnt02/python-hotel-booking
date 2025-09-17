"""
Custom exception handlers for the FastAPI application.
"""
from typing import Union
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from sqlalchemy.exc import IntegrityError, DataError, OperationalError
from pydantic import ValidationError
import structlog

from app.core.logging import get_logger

logger = get_logger(__name__)


class AppException(Exception):
    """Base application exception."""
    
    def __init__(
        self, 
        message: str, 
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: dict = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationException(AppException):
    """Validation error exception."""
    
    def __init__(self, message: str, details: dict = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details
        )


class AuthenticationException(AppException):
    """Authentication error exception."""
    
    def __init__(self, message: str = "Authentication failed", details: dict = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details
        )


class AuthorizationException(AppException):
    """Authorization error exception."""
    
    def __init__(self, message: str = "Not authorized", details: dict = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            details=details
        )


class NotFoundException(AppException):
    """Resource not found exception."""
    
    def __init__(self, message: str = "Resource not found", details: dict = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            details=details
        )


class ConflictException(AppException):
    """Resource conflict exception."""
    
    def __init__(self, message: str = "Resource conflict", details: dict = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            details=details
        )


class BusinessLogicException(AppException):
    """Business logic error exception."""
    
    def __init__(self, message: str, details: dict = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details
        )


class ExternalServiceException(AppException):
    """External service error exception."""
    
    def __init__(self, message: str = "External service error", details: dict = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details=details
        )


def get_request_id(request: Request) -> str:
    """Get request ID from request state."""
    return getattr(request.state, 'request_id', 'unknown')


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """
    Handle custom application exceptions.
    
    Args:
        request: HTTP request
        exc: Application exception
    
    Returns:
        JSON error response
    """
    request_id = get_request_id(request)
    
    logger.warning(
        "Application exception occurred",
        error=exc.message,
        status_code=exc.status_code,
        details=exc.details,
        request_id=request_id,
        path=request.url.path
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "message": exc.message,
                "details": exc.details,
                "request_id": request_id
            }
        }
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Handle FastAPI HTTP exceptions.
    
    Args:
        request: HTTP request
        exc: HTTP exception
    
    Returns:
        JSON error response
    """
    request_id = get_request_id(request)
    
    logger.warning(
        "HTTP exception occurred",
        error=exc.detail,
        status_code=exc.status_code,
        request_id=request_id,
        path=request.url.path
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "message": exc.detail,
                "request_id": request_id
            }
        }
    )


async def validation_exception_handler(
    request: Request, 
    exc: Union[RequestValidationError, ValidationError]
) -> JSONResponse:
    """
    Handle validation errors.
    
    Args:
        request: HTTP request
        exc: Validation exception
    
    Returns:
        JSON error response with validation details
    """
    request_id = get_request_id(request)
    
    # Format validation errors
    errors = []
    for error in exc.errors():
        errors.append({
            "field": " -> ".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })
    
    logger.warning(
        "Validation error occurred",
        errors=errors,
        request_id=request_id,
        path=request.url.path
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "message": "Validation failed",
                "details": {
                    "validation_errors": errors
                },
                "request_id": request_id
            }
        }
    )


async def database_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle database-related exceptions.
    
    Args:
        request: HTTP request
        exc: Database exception
    
    Returns:
        JSON error response
    """
    request_id = get_request_id(request)
    
    if isinstance(exc, IntegrityError):
        # Handle database constraint violations
        logger.warning(
            "Database integrity error",
            error=str(exc.orig),
            request_id=request_id,
            path=request.url.path
        )
        
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "error": {
                    "message": "Data integrity constraint violation",
                    "details": {
                        "database_error": "Resource already exists or constraint violated"
                    },
                    "request_id": request_id
                }
            }
        )
    
    elif isinstance(exc, DataError):
        # Handle data format errors
        logger.warning(
            "Database data error",
            error=str(exc.orig),
            request_id=request_id,
            path=request.url.path
        )
        
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": {
                    "message": "Invalid data format",
                    "details": {
                        "database_error": "Data format is invalid"
                    },
                    "request_id": request_id
                }
            }
        )
    
    elif isinstance(exc, OperationalError):
        # Handle database connection/operation errors
        logger.error(
            "Database operational error",
            error=str(exc.orig),
            request_id=request_id,
            path=request.url.path
        )
        
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "error": {
                    "message": "Database service unavailable",
                    "details": {
                        "database_error": "Database connection or operation failed"
                    },
                    "request_id": request_id
                }
            }
        )
    
    # Generic database error
    logger.error(
        "Unknown database error",
        error=str(exc),
        request_id=request_id,
        path=request.url.path
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "message": "Database error occurred",
                "request_id": request_id
            }
        }
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle any unhandled exceptions.
    
    Args:
        request: HTTP request
        exc: Generic exception
    
    Returns:
        JSON error response
    """
    request_id = get_request_id(request)
    
    logger.error(
        "Unhandled exception occurred",
        error=str(exc),
        error_type=type(exc).__name__,
        request_id=request_id,
        path=request.url.path,
        exc_info=True
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "message": "Internal server error",
                "request_id": request_id
            }
        }
    )


# Exception handler mapping
EXCEPTION_HANDLERS = {
    AppException: app_exception_handler,
    HTTPException: http_exception_handler,
    RequestValidationError: validation_exception_handler,
    ValidationError: validation_exception_handler,
    IntegrityError: database_exception_handler,
    DataError: database_exception_handler,
    OperationalError: database_exception_handler,
    Exception: generic_exception_handler,
}
