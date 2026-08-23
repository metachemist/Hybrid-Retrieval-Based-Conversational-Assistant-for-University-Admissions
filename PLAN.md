# Plan: Multi-Tenant Admin Dashboard + RAG Chatbot

## Context

The project currently has a single-role RAG chatbot. The goal is to split it into two distinct
experiences:

- **User side**: RAG chatbot (existing, now behind optional auth)
- **Admin side**: Analytics dashboard populated by chat data, plus document management

The dashboard mirrors the style in `image.png` (Higher Education Enrollment and Retention
Dashboard): KPI cards on the left, bar/line charts on the right, date range filter at the top.
Adapted for admission chatbot data: query volume, language distribution, topic breakdown,
response performance, and top questions.

Data flow: User submits query → backend classifies topic + logs metadata → admin dashboard reads
query_logs and aggregates into charts.

---

## New Packages Required

**Backend (`backend/requirements.txt`):**
```
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
```

**Frontend (`frontend/package.json`):**
```
recharts          # charts (ships its own TypeScript types, no @types needed)
```

---

## Database Changes

**File:** `backend/app/models/__init__.py`

1. Add `User` model (must be defined BEFORE QueryLog):
```python
class User(Base):
    __tablename__ = "users"
    id            = Column(String(36), primary_key=True, default=uuid4)
    email         = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role          = Column(String(20), default="user")   # "user" | "admin"
    created_at    = Column(DateTime, default=datetime.utcnow)
```

2. Add two columns to `QueryLog`:
```python
topic   = Column(String(50), nullable=True)   # classified query topic
user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
```

**SQLite migration note:** `Base.metadata.create_all()` does NOT add columns to existing tables.
Delete `backend/admission_demo.db` before restarting so schema is recreated from scratch.
In production (PostgreSQL), use an Alembic migration instead.

---

## Backend: New Files

### `backend/app/core/security.py`
JWT utilities:
- `hash_password(plain) -> str`
- `verify_password(plain, hashed) -> bool`
- `create_access_token(data) -> str`
- FastAPI dependency: `get_current_user(token) -> User` (auto_error=False variant for optional auth)
- FastAPI dependency: `require_admin(user) -> User` (raises 403 if role != admin)

### `backend/app/services/analytics/__init__.py`
Empty, makes `analytics` a Python package.

### `backend/app/services/analytics/topic_classifier.py`
Keyword-based classifier. Classifies against `normalized_query` (not raw text) so Roman Urdu
queries already translated by the normalizer still match:
```python
TOPIC_KEYWORDS = {
    "eligibility": ["eligible", "qualify", "criteria", "marks", "percentage", "inter", "matric"],
    "fees":        ["fee", "fees", "payment", "cost", "amount", "charges", "voucher", "kitna"],
    "documents":   ["document", "certificate", "transcript", "photo", "attested", "original", "kagaz"],
    "deadlines":   ["deadline", "last date", "schedule", "closing", "kab"],
    "merit":       ["merit", "result", "list", "selection", "rank", "aggregate"],
    "programs":    ["program", "course", "department", "faculty", "bs", "ms", "bba", "degree"],
    "application": ["apply", "application", "submit", "submission", "form", "chahiye", "kaise"],
}
def classify(query: str) -> str  # returns topic key or "general"
```

### `backend/app/api/auth.py`
```
POST /api/auth/register   body: {email, password, admin_key?}
                          admin_key matches ADMIN_REGISTRATION_KEY → role="admin", else "user"
                          admin_key never logged or returned
POST /api/auth/login      returns {access_token, token_type, role}
GET  /api/auth/me         returns {id, email, role}
```

### `backend/app/api/admin.py`
All routes protected by `require_admin`. All accept `?days=30` query param:
```
GET /api/admin/analytics/overview    total_queries, unique_users, avg_latency_ms,
                                     cache_hit_rate_pct, success_rate_pct
                                     (success = llm_provider != "none")
GET /api/admin/analytics/queries     [{date, count}] daily volume
GET /api/admin/analytics/languages   [{language, count}]
GET /api/admin/analytics/topics      [{topic, count}] sorted desc
GET /api/admin/analytics/performance avg_latency_ms, p95_latency_ms, cache_hit_rate, error_rate
                                     (error = llm_provider in ["none","fallback"])
GET /api/admin/analytics/top-queries [{query, count}] top 10 by exact text frequency
GET /api/admin/users                 [{id, email, role, created_at}]
```

---

## Backend: Modified Files

### `backend/app/core/config.py`
Add:
```python
SECRET_KEY: str = "change-me-in-production"
ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440   # 24 hours
ADMIN_REGISTRATION_KEY: str = "set-a-strong-secret-in-env"
```

### `backend/.env.example`
Add:
```
SECRET_KEY="change-me-in-production"
ACCESS_TOKEN_EXPIRE_MINUTES=1440
ADMIN_REGISTRATION_KEY="your-strong-admin-key"
```

### `backend/app/api/documents.py`
Add `require_admin` to: `upload_document`, `delete_document`, `reindex_document`.
List and stats endpoints stay public.

### `backend/app/api/chat.py`
- Call `classify(normalized_query)` after normalization → store as `topic` in QueryLog
- Extract optional `user_id` from JWT if Authorization header present

### `backend/app/__init__.py`
- Register `auth.router` and `admin.router`
- Wire slowapi rate limiter

### `backend/requirements.txt`
Add `python-jose[cryptography]>=3.3.0` and `passlib[bcrypt]>=1.7.4`

---

## Frontend: New Files

### `frontend/src/lib/auth.tsx`
- `AuthProvider`: JWT stored in localStorage, provides `user`, `token`, `login()`, `logout()`
- `useAuth()` hook
- On mount: decode stored token to restore session

### `frontend/src/app/login/page.tsx`
Email + password form → login → redirect admin→`/admin`, user→`/`

### `frontend/src/app/register/page.tsx`
Email + password + confirm password + optional collapsible "Admin Key" field
→ register → auto-login → redirect to `/`

### `frontend/src/app/admin/layout.tsx`
Protected: redirect to `/login` if not admin. Sidebar: Dashboard / Documents.

### `frontend/src/app/admin/page.tsx`
Dashboard layout (mirrors image.png):
```
Left:   Topic filter checkboxes | Date range (7/30/90 days) | 4 KPI cards
Right:  Query Volume line chart (top) | Language bar + Topic bar (bottom row)
```

### `frontend/src/app/admin/documents/page.tsx`
List documents | Upload PDF | Delete (with confirm) | Re-index button

### `frontend/src/components/admin/KpiCard.tsx`
Reusable card: value + label.

### `frontend/src/components/admin/QueryVolumeChart.tsx`
Recharts LineChart for daily query volume.

### `frontend/src/components/admin/LanguageChart.tsx`
Recharts BarChart for English / Roman Urdu / Mixed counts.

### `frontend/src/components/admin/TopicChart.tsx`
Recharts horizontal BarChart for the topic breakdown.

---

## Frontend: Modified Files

### `frontend/src/lib/api.ts`
- `setToken(t)` / `clearToken()` for auth injection
- `Authorization: Bearer` header on all requests when token is set
- Auth methods: `login()`, `register()`
- Admin methods: `getAnalyticsOverview()`, `getQueryVolume()`, `getLanguageStats()`,
  `getTopicStats()`, `getPerformanceStats()`, `getTopQueries()`, `getUsers()`

### `frontend/src/app/page.tsx`
- Replace inline `fetch` with `api.chat()`
- Auth-aware header: admin→show dashboard link, user→username+logout, anon→login link

### `frontend/src/app/layout.tsx`
Wrap with `<AuthProvider>`

### `frontend/package.json`
Add `recharts`

---

## Implementation Order

```
Step 1  Install packages: pip install python-jose passlib[bcrypt] + npm install recharts
Step 2  config.py: add SECRET_KEY, ADMIN_REGISTRATION_KEY, ACCESS_TOKEN_EXPIRE_MINUTES
Step 3  .env.example: add the 3 new vars
Step 4  security.py: JWT utils + FastAPI dependencies
Step 5  models/__init__.py: User model (before QueryLog) + topic/user_id on QueryLog
        → delete admission_demo.db
Step 6  services/analytics/__init__.py (empty)
Step 7  services/analytics/topic_classifier.py
Step 8  api/auth.py: register, login, me
Step 9  api/admin.py: all analytics + users endpoints
Step 10 api/documents.py: admin protection on write endpoints
Step 11 api/chat.py: topic classification + optional user_id
Step 12 app/__init__.py: register routers + wire rate limiter
Step 13 frontend/src/lib/api.ts: token injection + all new methods
Step 14 frontend/src/lib/auth.tsx: AuthProvider + useAuth
Step 15 frontend/src/app/layout.tsx: AuthProvider wrapper
Step 16 frontend/src/app/login/page.tsx
Step 17 frontend/src/app/register/page.tsx
Step 18 frontend/src/app/page.tsx: api.chat() + auth-aware header
Step 19 frontend/src/app/admin/layout.tsx: protected sidebar layout
Step 20 frontend/src/components/admin/KpiCard.tsx
Step 21 frontend/src/components/admin/QueryVolumeChart.tsx
Step 22 frontend/src/components/admin/LanguageChart.tsx
Step 23 frontend/src/components/admin/TopicChart.tsx
Step 24 frontend/src/app/admin/page.tsx: assembles all
Step 25 frontend/src/app/admin/documents/page.tsx
```

---

## Verification

1. `POST /api/auth/register` with `admin_key` → `POST /api/auth/login` → `GET /api/auth/me` returns `role: admin`
2. `GET /api/admin/analytics/overview`: no token gives 401, user token → 403, admin token → 200
3. Query "documents chahiye" → `query_logs.topic` = "documents"
4. `/login` → redirect to `/admin` → dashboard renders with KPI cards and charts
5. `/admin/documents` → upload PDF → appears in list → delete → removed
