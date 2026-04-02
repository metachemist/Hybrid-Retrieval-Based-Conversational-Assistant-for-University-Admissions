"""
Database initialization script.

Creates tables and enables pgvector extension.
Run this once before starting the application.

Usage:
    python scripts/init_db.py
"""
import sys
sys.path.insert(0, 'backend')

from sqlalchemy import text
from app.core.database import engine, Base
from app.core.config import settings


def init_database():
    """Initialize the database with required extensions and tables."""
    print("Initializing database...")
    
    # Create all tables
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    
    # Enable pgvector extension
    print("Enabling pgvector extension...")
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()
    
    # Verify setup
    print("Verifying setup...")
    with engine.connect() as conn:
        result = conn.execute(text("SELECT extname FROM pg_extension WHERE extname = 'vector'"))
        if result.fetchone():
            print("✓ pgvector extension enabled")
        else:
            print("✗ pgvector extension not found")
    
    print("\nDatabase initialization complete!")
    print(f"Database: {settings.DATABASE_URL.split('@')[-1]}")


if __name__ == "__main__":
    init_database()
