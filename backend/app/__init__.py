"""
Rehnuma - University of Karachi admissions assistant, FastAPI Backend
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
import sentry_sdk
from .core.config import settings
from .core.ratelimit import limiter
from .api import chat, documents, health, auth, admin


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="Rehnuma: hybrid RAG-based conversational assistant for University of Karachi admission policies"
    )

    # Rate limiting — the shared limiter is applied per-route via
    # @limiter.limit(...) decorators (see app/api/chat.py, app/api/auth.py).
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Configure Sentry for error tracking
    if settings.SENTRY_DSN:
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            traces_sample_rate=0.1,
            profiles_sample_rate=0.1,
        )

    # Include routers
    app.include_router(auth.router, prefix="/api", tags=["auth"])
    app.include_router(admin.router, prefix="/api", tags=["admin"])
    app.include_router(chat.router, prefix="/api", tags=["chat"])
    app.include_router(documents.router, prefix="/api", tags=["documents"])
    app.include_router(health.router, prefix="/api", tags=["health"])
    
    @app.get("/")
    async def root():
        """Root endpoint."""
        return {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "status": "running"
        }
    
    return app


app = create_app()
