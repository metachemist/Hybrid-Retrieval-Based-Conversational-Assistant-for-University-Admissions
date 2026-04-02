"""
Admission Policy Chatbot - FastAPI Backend
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sentry_sdk
from .core.config import settings
from .core.database import engine, Base
from .api import chat, documents, health

# Create database tables
Base.metadata.create_all(bind=engine)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="Hybrid RAG-based conversational assistant for university admission policies"
    )
    
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
