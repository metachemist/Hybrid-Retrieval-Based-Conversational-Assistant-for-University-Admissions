"""
SQLAlchemy models for the admission chatbot database.
Requires PostgreSQL with the pgvector extension.
"""
import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column, String, Integer, DateTime, ForeignKey,
    Text, Boolean, Float, event, Computed, Index
)
from sqlalchemy.dialects.postgresql import UUID, TSVECTOR
from sqlalchemy.orm import relationship, validates
from pgvector.sqlalchemy import Vector
from ..core.database import Base

EMBEDDING_DIMENSION = 1536  # openai text-embedding-3-small


class User(Base):
    """Model for authenticated users (admin and regular)."""

    __tablename__ = "users"

    id                   = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email                = Column(String(255), unique=True, nullable=False, index=True)
    password_hash        = Column(String(255), nullable=False)
    role                 = Column(String(20), default="user")   # "user" | "admin"
    created_at           = Column(DateTime, default=datetime.utcnow)
    reset_token          = Column(String(100), nullable=True)
    reset_token_expires  = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"


class Document(Base):
    """Model for storing admission document metadata."""
    
    __tablename__ = "documents"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(500), nullable=False)
    year = Column(Integer, nullable=True)
    source_path = Column(String(500), nullable=True)
    ingested_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship to chunks
    chunks = relationship("Chunk", back_populates="document", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Document(id={self.id}, title='{self.title}')>"


class Chunk(Base):
    """Model for storing document chunks with embeddings."""
    
    __tablename__ = "chunks"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    doc_id = Column(String(36), ForeignKey("documents.id"), nullable=False)
    content = Column(Text, nullable=False)
    embedding = Column(Vector(EMBEDDING_DIMENSION), nullable=True)
    section_header = Column(String(300), nullable=True)
    page_start = Column(Integer, nullable=True)
    page_end = Column(Integer, nullable=True)
    chunk_type = Column(String(50), default="text")
    chunk_order = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Postgres-generated (see migration 7c3e1f9a2b58): to_tsvector() is
    # computed at write time so keyword search can hit a GIN index instead of
    # re-tokenizing every chunk on every query. Never assign to this.
    content_tsv = Column(
        TSVECTOR,
        Computed("to_tsvector('english', content)", persisted=True),
        nullable=True,
    )

    # Relationship to document
    document = relationship("Document", back_populates="chunks")

    # Declared here as well as in migration 7c3e1f9a2b58 so that a database
    # built by init_db()/create_all() gets the same indexes as a migrated one.
    # The deployed database was built the create_all() way and then stamped,
    # which is exactly why it reached production with no retrieval indexes at all.
    __table_args__ = (
        Index('chunks_doc_id_idx', 'doc_id'),
        Index('chunks_content_tsv_idx', 'content_tsv', postgresql_using='gin'),
        Index(
            'chunks_embedding_hnsw_idx', 'embedding',
            postgresql_using='hnsw',
            postgresql_ops={'embedding': 'vector_cosine_ops'},
        ),
    )

    def __repr__(self):
        return f"<Chunk(id={self.id}, doc_id={self.doc_id}, page={self.page_start})>"


class QueryLog(Base):
    """Model for logging user queries for analytics."""
    
    __tablename__ = "query_logs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    query_text = Column(Text, nullable=False)
    detected_language = Column(String(20), nullable=True)
    normalized_query = Column(Text, nullable=True)
    response = Column(Text, nullable=True)
    latency_ms = Column(Integer, nullable=True)
    cache_hit = Column(Boolean, default=False)
    llm_provider = Column(String(50), nullable=True)
    retrieval_scores = Column(Text, nullable=True)
    topic = Column(String(50), nullable=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f"<QueryLog(id={self.id}, query='{self.query_text[:50]}...')>"
