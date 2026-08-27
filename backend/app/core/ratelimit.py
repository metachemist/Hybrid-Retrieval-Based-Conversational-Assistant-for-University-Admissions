"""
Shared slowapi rate limiter.

Lives in its own module so route handlers and app setup import the *same*
Limiter instance. Storage is in-process memory, which is correct for a
single-instance deployment; a multi-instance deploy would point
``storage_uri`` at Redis.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

from .config import settings

# Trust the platform's forwarded-for header so the limiter keys on the real
# client IP rather than the Render/Vercel proxy that fronts every request.
def _client_ip(request):
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return get_remote_address(request)


# headers_enabled stays off: injecting X-RateLimit-* headers requires every
# limited endpoint to take a `response: Response` param, and the sync /chat
# handler returns a Pydantic model. Enforcement works regardless.
limiter = Limiter(key_func=_client_ip, headers_enabled=False)

# Limit string applied to the chat endpoints, built from settings.
CHAT_RATE_LIMIT = (
    f"{settings.RATE_LIMIT_PER_MINUTE}/minute;{settings.RATE_LIMIT_PER_HOUR}/hour"
)

# Tighter limit for credential endpoints to slow brute-force / stuffing.
AUTH_RATE_LIMIT = "10/minute;60/hour"
