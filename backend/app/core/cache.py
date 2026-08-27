"""
Redis-backed response cache for chat answers.

Degrades gracefully: if REDIS_URL is unset or Redis cannot be reached, every
operation becomes a no-op and the app runs uncached rather than failing. The
first connection error disables the client for the process so a down Redis
does not add latency to every subsequent request.
"""
import hashlib
import json
import logging
from typing import Optional

from .config import settings

logger = logging.getLogger(__name__)

_redis = None
_disabled = False


def _client():
    global _redis, _disabled
    if _disabled:
        return None
    if _redis is not None:
        return _redis
    if not settings.REDIS_URL:
        _disabled = True
        return None
    try:
        import redis

        client = redis.Redis.from_url(
            settings.REDIS_URL,
            socket_connect_timeout=1,
            socket_timeout=1,
            decode_responses=True,
        )
        client.ping()
    except Exception as exc:  # noqa: BLE001 - any failure means "no cache"
        logger.warning("Response cache disabled (Redis unavailable): %s", exc)
        _disabled = True
        return None
    _redis = client
    return _redis


def make_key(query: str, top_k: int, use_hybrid: bool) -> str:
    raw = f"{query.strip().lower()}|{top_k}|{int(use_hybrid)}"
    return "chat:" + hashlib.sha1(raw.encode("utf-8")).hexdigest()


def get_cached(key: str) -> Optional[dict]:
    client = _client()
    if client is None:
        return None
    try:
        raw = client.get(key)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Cache read failed: %s", exc)
        return None
    if not raw:
        return None
    try:
        return json.loads(raw)
    except (ValueError, TypeError):
        return None


def set_cached(key: str, value: dict, ttl: Optional[int] = None) -> None:
    client = _client()
    if client is None:
        return
    try:
        client.set(key, json.dumps(value), ex=ttl or settings.CACHE_TTL_SECONDS)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Cache write failed: %s", exc)
