"""
Database session management and base model configuration.
Requires PostgreSQL with the pgvector extension.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from .config import settings

DATABASE_URL = settings.DATABASE_URL

# Create database engine
engine = create_engine(
    DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db():
    """Dependency for getting database session in FastAPI routes."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables."""
    from ..models import Document, Chunk, QueryLog  # noqa: F401 - registers tables for create_all
    Base.metadata.create_all(bind=engine)
    print("✓ Database initialized")
