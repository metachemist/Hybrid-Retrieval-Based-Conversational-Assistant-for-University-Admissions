"""
Configuration settings for the admission chatbot backend.
Loads environment variables and provides type-safe configuration.
"""
from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    APP_NAME: str = "Rehnuma"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/admission_db"
    
    # Embeddings (using OpenAI API for development; switch to multilingual-e5-large for production)
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_DIMENSION: int = 1536
    
    # LLM Providers
    OPENAI_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    
    # LLM Settings
    LLM_TEMPERATURE: float = 0.3
    LLM_MAX_TOKENS: int = 1024
    
    # Retrieval Settings
    RETRIEVAL_TOP_K: int = 20
    RRF_K: int = 60
    RRF_WEIGHT_KEYWORD: float = 0.5
    RRF_WEIGHT_SEMANTIC: float = 0.5
    
    # Caching
    REDIS_URL: str = "redis://localhost:6379"
    CACHE_TTL_SECONDS: int = 86400  # 24 hours
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 10
    RATE_LIMIT_PER_HOUR: int = 100
    
    # Auth
    SECRET_KEY: str = "change-me-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    ADMIN_REGISTRATION_KEY: str = "set-a-strong-secret-in-env"

    # Password reset
    FRONTEND_URL: str = "http://localhost:3000"
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM: Optional[str] = None

    # Monitoring
    SENTRY_DSN: Optional[str] = None
    
    # CORS
    CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:8080"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
