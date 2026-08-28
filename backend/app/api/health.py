"""
Health Check API Endpoints

Provides system health and status information.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text, func
from pydantic import BaseModel
import time

from ..core.database import get_db
from ..core.config import settings
from ..models import Document, Chunk, QueryLog
from ..services.rag.llm_provider import get_llm_provider

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    uptime_seconds: int
    database: str
    llm_provider: str
    documents_count: int
    chunks_count: int


class DatabaseHealth(BaseModel):
    """Database health status."""
    status: str
    connection_time_ms: int
    documents_count: int
    chunks_count: int


class LLMHealth(BaseModel):
    """LLM provider health status."""
    status: str
    provider: str
    available_providers: list


@router.get("/health", response_model=HealthResponse)
async def health_check(db: Session = Depends(get_db)):
    """
    Comprehensive health check.
    
    Checks:
    - Database connectivity
    - LLM provider availability
    - System statistics
    """
    # Check database
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "disconnected"
    
    # Check LLM provider
    llm = get_llm_provider()
    llm_status = llm.get_current_provider()
    
    # Get statistics
    doc_count = db.query(Document).count()
    chunk_count = db.query(Chunk).count()
    
    return HealthResponse(
        status="healthy" if db_status == "connected" else "unhealthy",
        version=settings.APP_VERSION,
        uptime_seconds=0,  # Would need to track app start time
        database=db_status,
        llm_provider=llm_status,
        documents_count=doc_count,
        chunks_count=chunk_count
    )


@router.get("/health/db", response_model=DatabaseHealth)
async def database_health(db: Session = Depends(get_db)):
    """Check database connectivity and statistics."""
    start_time = time.time()
    
    try:
        db.execute(text("SELECT 1"))
        connection_time = int((time.time() - start_time) * 1000)
        
        doc_count = db.query(Document).count()
        chunk_count = db.query(Chunk).count()
        
        return DatabaseHealth(
            status="connected",
            connection_time_ms=connection_time,
            documents_count=doc_count,
            chunks_count=chunk_count
        )
    except Exception:
        return DatabaseHealth(
            status="disconnected",
            connection_time_ms=0,
            documents_count=0,
            chunks_count=0
        )


@router.get("/health/llm", response_model=LLMHealth)
async def llm_health():
    """Check LLM provider availability."""
    llm = get_llm_provider()
    
    available = []
    for provider in llm.providers:
        if provider.is_available:
            available.append(provider.name)
    
    current = llm.get_current_provider()
    
    return LLMHealth(
        status="available" if current != "none" else "unavailable",
        provider=current,
        available_providers=available
    )


@router.get("/health/query-stats")
async def query_stats(
    hours: int = 24,
    db: Session = Depends(get_db)
):
    """Get query statistics for the specified time period."""
    from datetime import datetime, timedelta
    
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    
    # Count queries
    total_queries = db.query(QueryLog).filter(QueryLog.created_at >= cutoff).count()
    
    # Average latency
    avg_latency = db.query(
        QueryLog.latency_ms
    ).filter(
        QueryLog.created_at >= cutoff,
        QueryLog.latency_ms.isnot(None)
    ).all()
    
    avg_latency_ms = sum(l[0] for l in avg_latency) / len(avg_latency) if avg_latency else 0
    
    # Cache hit rate
    cache_hits = db.query(QueryLog).filter(
        QueryLog.created_at >= cutoff,
        QueryLog.cache_hit == True
    ).count()
    
    cache_hit_rate = (cache_hits / total_queries * 100) if total_queries > 0 else 0
    
    # Language distribution
    lang_stats = db.query(
        QueryLog.detected_language,
        func.count(QueryLog.id)
    ).filter(
        QueryLog.created_at >= cutoff
    ).group_by(QueryLog.detected_language).all()
    
    return {
        "time_period_hours": hours,
        "total_queries": total_queries,
        "average_latency_ms": round(avg_latency_ms, 2),
        "cache_hit_rate_percent": round(cache_hit_rate, 2),
        "language_distribution": {lang: count for lang, count in lang_stats}
    }
