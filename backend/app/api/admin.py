"""
Admin API Endpoints — analytics dashboard data and user management.

All routes require admin role.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, case, distinct
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List

from ..core.database import get_db
from ..core.security import require_admin
from ..models import QueryLog, User, Document, Chunk

router = APIRouter()

# llm_provider values that mean "no real answer was produced".
_FAILURE_PROVIDERS = ("none", "fallback", "error")


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

    # One aggregate round trip instead of pulling every row into Python.
    row = db.query(
        func.count(QueryLog.id).label("total"),
        func.count(distinct(QueryLog.user_id)).label("unique_users"),
        func.avg(QueryLog.latency_ms).label("avg_latency"),
        func.sum(case((QueryLog.cache_hit.is_(True), 1), else_=0)).label("cache_hits"),
        func.sum(
            case((QueryLog.llm_provider.notin_(_FAILURE_PROVIDERS), 1), else_=0)
        ).label("successes"),
    ).filter(QueryLog.created_at >= since).one()

    total = row.total or 0
    return {
        "days": days,
        "total_queries": total,
        "unique_users": row.unique_users or 0,
        "avg_latency_ms": round(float(row.avg_latency), 1) if row.avg_latency is not None else 0,
        "cache_hit_rate_pct": round((row.cache_hits or 0) / total * 100, 1) if total else 0,
        "success_rate_pct": round((row.successes or 0) / total * 100, 1) if total else 0,
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

    row = db.query(
        func.count(QueryLog.id).label("total"),
        func.avg(QueryLog.latency_ms).label("avg_latency"),
        func.percentile_cont(0.95)
        .within_group(QueryLog.latency_ms.asc())
        .label("p95_latency"),
        func.sum(case((QueryLog.cache_hit.is_(True), 1), else_=0)).label("cache_hits"),
        func.sum(
            case((QueryLog.llm_provider.in_(_FAILURE_PROVIDERS), 1), else_=0)
        ).label("errors"),
    ).filter(QueryLog.created_at >= since).one()

    total = row.total or 0
    return {
        "days": days,
        "total_queries": total,
        "avg_latency_ms": round(float(row.avg_latency), 1) if row.avg_latency is not None else 0,
        "p95_latency_ms": round(float(row.p95_latency)) if row.p95_latency is not None else 0,
        "cache_hit_rate_pct": round((row.cache_hits or 0) / total * 100, 1) if total else 0,
        "error_rate_pct": round((row.errors or 0) / total * 100, 1) if total else 0,
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
