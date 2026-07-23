"""
ClauseIQ — Custom Exception Classes & Handlers

Domain exceptions are raised by services and mapped to HTTP responses
by global exception handlers registered in main.py.
Services never raise HTTPException directly — that's a router-layer concern.
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse


# =============================================================================
# Base Exception
# =============================================================================

class ClauseIQError(Exception):
    """Base exception for all ClauseIQ domain errors."""

    def __init__(self, message: str = "An unexpected error occurred"):
        self.message = message
        super().__init__(self.message)


# =============================================================================
# Authentication & Authorization Errors
# =============================================================================

class AuthenticationError(ClauseIQError):
    """Raised when authentication fails (bad credentials, expired token)."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message)


class AuthorizationError(ClauseIQError):
    """Raised when a user tries to access a resource they don't own."""

    def __init__(self, message: str = "You do not have permission to access this resource"):
        super().__init__(message)


# =============================================================================
# Resource Errors
# =============================================================================

class ResourceNotFoundError(ClauseIQError):
    """Raised when a requested resource does not exist."""

    def __init__(self, resource_type: str, resource_id: str | int):
        self.resource_type = resource_type
        self.resource_id = resource_id
        super().__init__(f"{resource_type} with id '{resource_id}' not found")


class DuplicateResourceError(ClauseIQError):
    """Raised when a resource with the same unique constraint already exists."""

    def __init__(self, message: str = "A resource with this identifier already exists"):
        super().__init__(message)


# =============================================================================
# File / Upload Errors
# =============================================================================

class FileValidationError(ClauseIQError):
    """Raised when an uploaded file fails validation (type, size)."""

    def __init__(self, message: str = "File validation failed"):
        super().__init__(message)


# =============================================================================
# Processing Errors
# =============================================================================

class ProcessingFailedError(ClauseIQError):
    """Raised when document processing or an AI workflow fails."""

    def __init__(self, message: str = "Document processing failed"):
        super().__init__(message)


class AIServiceError(ClauseIQError):
    """Raised when an AI service call (Groq, embeddings) fails."""

    def __init__(self, message: str = "AI service encountered an error"):
        super().__init__(message)


# =============================================================================
# Exception Handlers (registered in main.py)
# =============================================================================

async def authentication_error_handler(request: Request, exc: AuthenticationError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": exc.message},
    )


async def authorization_error_handler(request: Request, exc: AuthorizationError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={"detail": exc.message},
    )


async def resource_not_found_handler(request: Request, exc: ResourceNotFoundError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": exc.message},
    )


async def duplicate_resource_handler(request: Request, exc: DuplicateResourceError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": exc.message},
    )


async def file_validation_error_handler(request: Request, exc: FileValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.message},
    )


async def processing_failed_handler(request: Request, exc: ProcessingFailedError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": exc.message},
    )


async def ai_service_error_handler(request: Request, exc: AIServiceError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content={"detail": exc.message},
    )


async def general_error_handler(request: Request, exc: ClauseIQError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": exc.message},
    )
