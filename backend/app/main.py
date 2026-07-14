"""
ClauseIQ — FastAPI Application Entry Point

App instantiation, middleware configuration, router registration,
and global exception handler registration per AGENT.md Section 6.2.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.core.exceptions import (
    AIServiceError,
    AuthenticationError,
    AuthorizationError,
    ClauseIQError,
    DuplicateResourceError,
    FileValidationError,
    ProcessingFailedError,
    ResourceNotFoundError,
    ai_service_error_handler,
    authentication_error_handler,
    authorization_error_handler,
    duplicate_resource_handler,
    file_validation_error_handler,
    general_error_handler,
    processing_failed_handler,
    resource_not_found_handler,
)
from app.core.logging_config import get_logger, setup_logging

# --- Routers ---
from app.api.v1.auth import router as auth_router
from app.api.v1.projects import router as projects_router
from app.api.v1.contracts import router as contracts_router
from app.api.v1.chat import router as chat_router
from app.api.v1.clauses import router as clauses_router
from app.api.v1.risks import router as risks_router
from app.api.v1.summaries import router as summaries_router
from app.api.v1.comparisons import router as comparisons_router
from app.api.v1.search import router as search_router
from app.api.v1.dashboard import router as dashboard_router

logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle."""
    setup_logging()
    logger.info(
        "%s v%s starting up", settings.APP_NAME, settings.APP_VERSION
    )
    yield
    logger.info("%s shutting down", settings.APP_NAME)


def create_app() -> FastAPI:
    """Factory function that builds and configures the FastAPI application."""
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="AI-powered Enterprise Contract Intelligence Platform",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # --- CORS Middleware ---
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- Exception Handlers ---
    app.add_exception_handler(AuthenticationError, authentication_error_handler)
    app.add_exception_handler(AuthorizationError, authorization_error_handler)
    app.add_exception_handler(ResourceNotFoundError, resource_not_found_handler)
    app.add_exception_handler(DuplicateResourceError, duplicate_resource_handler)
    app.add_exception_handler(FileValidationError, file_validation_error_handler)
    app.add_exception_handler(ProcessingFailedError, processing_failed_handler)
    app.add_exception_handler(AIServiceError, ai_service_error_handler)
    app.add_exception_handler(ClauseIQError, general_error_handler)

    # --- Routers ---
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(projects_router, prefix="/api/v1")
    app.include_router(contracts_router, prefix="/api/v1")
    app.include_router(chat_router, prefix="/api/v1")
    app.include_router(clauses_router, prefix="/api/v1")
    app.include_router(risks_router, prefix="/api/v1")
    app.include_router(summaries_router, prefix="/api/v1")
    app.include_router(comparisons_router, prefix="/api/v1")
    app.include_router(search_router, prefix="/api/v1")
    app.include_router(dashboard_router, prefix="/api/v1")

    # --- Health Check ---
    @app.get("/health", tags=["Health"])
    async def health_check():
        return {"status": "healthy", "app": settings.APP_NAME, "version": settings.APP_VERSION}

    return app


app = create_app()
