"""
Configuration settings for the admission chatbot backend.
Loads environment variables and provides type-safe configuration.
"""
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


# Placeholder values shipped in .env.example. The app refuses to start with any
# of these still in place unless DEBUG is on, so a misconfigured production
# deploy fails loudly instead of signing tokens with a public key.
INSECURE_DEFAULTS = {
    "SECRET_KEY": {"change-me-in-production", ""},
    "ADMIN_REGISTRATION_KEY": {"set-a-strong-secret-in-env", "your-strong-admin-key", ""},
}


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
    OPENAI_MODEL: str = "gpt-4o"
    # Gemini model id for the fallback provider. Kept in env because Google
    # rotates these faster than we redeploy; set it to whatever is current.
    GEMINI_MODEL: str = "gemini-3.6-flash"

    # Where uploaded source PDFs are written. Relative paths resolve against the
    # process working directory. NOTE: on an ephemeral filesystem (e.g. Render's
    # free tier) anything written here is lost on redeploy, which breaks
    # /documents/{id}/reindex — point this at a mounted disk or object storage
    # for durable uploads.
    UPLOAD_DIR: str = "data/raw"

    # Retrieval Settings
    RETRIEVAL_TOP_K: int = 20
    RRF_K: int = 60
    RRF_WEIGHT_KEYWORD: float = 0.5
    RRF_WEIGHT_SEMANTIC: float = 0.5

    # Caching
    REDIS_URL: Optional[str] = "redis://localhost:6379"
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

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )

    @model_validator(mode="after")
    def _reject_insecure_defaults(self) -> "Settings":
        if self.DEBUG:
            return self
        offenders = [
            name
            for name, bad_values in INSECURE_DEFAULTS.items()
            if getattr(self, name) in bad_values
        ]
        if offenders:
            raise ValueError(
                "Refusing to start with placeholder secrets: "
                + ", ".join(offenders)
                + ". Set them in the environment, or set DEBUG=true for local use."
            )
        return self


# Global settings instance
settings = Settings()
