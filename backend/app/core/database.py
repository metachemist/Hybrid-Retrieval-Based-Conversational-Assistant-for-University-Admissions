"""
Database session management and base model configuration.
Supports both PostgreSQL (production) and SQLite (demo).
"""
import os
from sqlalchemy import create_engine, event, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings

# Use SQLite for demo if PostgreSQL is not available
DATABASE_URL = settings.DATABASE_URL

# Detect if we should use SQLite demo mode
USE_SQLITE = False
if 'sqlite' in DATABASE_URL or 'localhost' not in DATABASE_URL.split('@')[0]:
    # Check if PostgreSQL is actually accessible
    try:
        test_engine = create_engine(DATABASE_URL)
        with test_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        test_engine.dispose()
    except Exception:
        USE_SQLITE = True
        DATABASE_URL = "sqlite:///./admission_demo.db"
        print(f"⚠️  PostgreSQL not available, using SQLite demo mode")
        print("   For production, set DATABASE_URL to a PostgreSQL connection string")

# Create database engine
if USE_SQLITE:
    engine = create_engine(
        DATABASE_URL,
        echo=settings.DEBUG,
        connect_args={"check_same_thread": False}
    )
else:
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
    from ..models import Document, Chunk, QueryLog  # Import all models
    Base.metadata.create_all(bind=engine)
    print("✓ Database initialized")
