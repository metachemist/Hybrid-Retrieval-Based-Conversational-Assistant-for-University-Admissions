"""
Admin API Endpoints — analytics dashboard data and user management.

All routes require admin role.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, case
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List

from ..core.database import get_db
from ..core.security import require_admin
from ..models import QueryLog, User, Document, Chunk

router = APIRouter()


def _cutoff(days: int) -> datetime:
    return datetime.utcnow() - timedelta(days=days)


@router.get("/admin/analytics/overview")
def analytics_overview(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    """KPI cards: total queries, unique users, avg latency, cache hit rate, success rate."""
    since = _cutoff(days)
    logs = db.query(QueryLog).filter(QueryLog.created_at >= since).all()

    total = len(logs)
    unique_users = len({l.user_id for l in logs if l.user_id})
    avg_latency = round(sum(l.latency_ms for l in logs if l.latency_ms) / total, 1) if total else 0
    cache_hits = sum(1 for l in logs if l.cache_hit)
    cache_hit_rate = round(cache_hits / total * 100, 1) if total else 0
    # success = got an LLM response (not "none" fallback)
    successes = sum(1 for l in logs if l.llm_provider and l.llm_provider not in ("none", "fallback"))
    success_rate = round(successes / total * 100, 1) if total else 0

    return {
        "days": days,
        "total_queries": total,
        "unique_users": unique_users,
        "avg_latency_ms": avg_latency,
        "cache_hit_rate_pct": cache_hit_rate,
        "success_rate_pct": success_rate,
    }


@router.get("/admin/analytics/queries")
def analytics_query_volume(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    """Daily query volume for the last N days."""
    since = _cutoff(days)

    rows = (
        db.query(
            func.date(QueryLog.created_at).label("date"),
            func.count(QueryLog.id).label("count"),
        )
        .filter(QueryLog.created_at >= since)
        .group_by(func.date(QueryLog.created_at))
        .order_by(func.date(QueryLog.created_at))
        .all()
    )

    return [{"date": str(r.date), "count": r.count} for r in rows]


@router.get("/admin/analytics/languages")
def analytics_languages(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    """Query count by detected language."""
    since = _cutoff(days)

    rows = (
        db.query(
            QueryLog.detected_language.label("language"),
            func.count(QueryLog.id).label("count"),
        )
        .filter(QueryLog.created_at >= since)
        .group_by(QueryLog.detected_language)
        .order_by(func.count(QueryLog.id).desc())
        .all()
    )

    return [{"language": r.language or "unknown", "count": r.count} for r in rows]


@router.get("/admin/analytics/topics")
def analytics_topics(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    """Query count by topic, sorted descending."""
    since = _cutoff(days)

    rows = (
        db.query(
            QueryLog.topic.label("topic"),
            func.count(QueryLog.id).label("count"),
        )
        .filter(QueryLog.created_at >= since)
        .group_by(QueryLog.topic)
        .order_by(func.count(QueryLog.id).desc())
        .all()
    )

    return [{"topic": r.topic or "general", "count": r.count} for r in rows]


@router.get("/admin/analytics/performance")
def analytics_performance(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    """Latency stats, cache hit rate, error rate."""
    since = _cutoff(days)
    logs = db.query(QueryLog).filter(QueryLog.created_at >= since).all()

    total = len(logs)
    latencies = sorted([l.latency_ms for l in logs if l.latency_ms])
    avg_latency = round(sum(latencies) / len(latencies), 1) if latencies else 0
    p95_latency = latencies[int(len(latencies) * 0.95)] if latencies else 0
    cache_hits = sum(1 for l in logs if l.cache_hit)
    errors = sum(1 for l in logs if l.llm_provider in ("none", "fallback"))

    return {
        "days": days,
        "total_queries": total,
        "avg_latency_ms": avg_latency,
        "p95_latency_ms": p95_latency,
        "cache_hit_rate_pct": round(cache_hits / total * 100, 1) if total else 0,
        "error_rate_pct": round(errors / total * 100, 1) if total else 0,
    }


@router.get("/admin/analytics/top-queries")
def analytics_top_queries(
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    """Top N most frequently asked queries (exact text match)."""
    since = _cutoff(days)

    rows = (
        db.query(
            QueryLog.query_text.label("query"),
            func.count(QueryLog.id).label("count"),
        )
        .filter(QueryLog.created_at >= since)
        .group_by(QueryLog.query_text)
        .order_by(func.count(QueryLog.id).desc())
        .limit(limit)
        .all()
    )

    return [{"query": r.query, "count": r.count} for r in rows]


@router.get("/admin/users")
def list_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    """List all registered users."""
    users = db.query(User).offset(skip).limit(limit).all()
    return [
        {"id": u.id, "email": u.email, "role": u.role, "created_at": u.created_at.isoformat()}
        for u in users
    ]
