"""
Database session management and base model configuration.
Requires PostgreSQL with the pgvector extension.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from .config import settings

DATABASE_URL = settings.DATABASE_URL

# Create database engine.
# pool_recycle drops connections older than 30 min so a stale one is never
# handed out — cheaper than pool_pre_ping, which fired a `SELECT 1` round trip
# to the (cross-region) database on every single checkout.
engine = create_engine(
    DATABASE_URL,
    echo=settings.DEBUG,
    pool_recycle=1800,
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
