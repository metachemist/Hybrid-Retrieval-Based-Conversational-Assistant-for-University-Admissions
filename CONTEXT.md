# Project Context: Admission Policy Chatbot

> **Last Updated:** April 2, 2026
> **Branch:** `initial-prototype`
> **Commit:** `909f266`
> **Status:** ✅ Running (Backend: :8000, Frontend: :3000)

---

## 1. Project Overview

### 1.1 Title
Design and Implementation of a Hybrid Retrieval-Based Conversational Assistant for University Admission Policies

### 1.2 Institution
University of Karachi — Final Year Project (FYP)

### 1.3 Supervisor
Miss Humaira Tariq

### 1.4 Problem Statement
Prospective students at the University of Karachi face difficulties understanding admission policies due to:
- Complex documentation in lengthy PDF documents
- Dispersed information sources
- Lack of interactive guidance
- No intelligent system for instant, reliable responses to informal queries
- Roman Urdu queries are common but unsupported by existing systems

### 1.5 Solution
A **Retrieval-Augmented Generation (RAG)** conversational assistant that:
- Processes official admission PDF documents
- Answers queries in **English, Roman Urdu, and code-mixed** text
- Provides **citation-grounded responses** linked to source documents
- Uses **hybrid retrieval** (keyword + semantic search with RRF fusion)
- Offers **LLM fallback chain** (Anthropic → OpenAI → Local Ollama)

---

## 2. Current Project State

### 2.1 What's Built ✅

| Component | Status | Location |
|-----------|--------|----------|
| Backend FastAPI Server | ✅ Running | `http://localhost:8000` |
| Frontend Next.js App | ✅ Running | `http://localhost:3000` |
| Roman Urdu Detection | ✅ Complete | `backend/app/services/roman_urdu/language_detection.py` |
| Roman Urdu Normalization | ✅ Complete | `backend/app/services/roman_urdu/normalization.py` |
| Hybrid Retrieval Engine | ✅ Complete | `backend/app/services/retrieval/hybrid_retriever.py` |
| Embedding Service | ✅ Complete (OpenAI) | `backend/app/services/retrieval/embeddings.py` |
| LLM Provider (3-tier fallback) | ✅ Complete | `backend/app/services/rag/llm_provider.py` |
| RAG Prompt Builder | ✅ Complete | `backend/app/services/rag/prompt.py` |
| Document Ingestion | ✅ Complete | `backend/app/services/retrieval/pdf_processor.py` + `scripts/ingest_documents.py` |
| Chat API Endpoint | ✅ Complete | `backend/app/api/chat.py` |
| Documents API | ✅ Complete | `backend/app/api/documents.py` |
| Health API | ✅ Complete | `backend/app/api/health.py` |
| Web Chat Interface | ✅ Complete | `frontend/src/app/page.tsx` |
| Citation Display | ✅ Complete | `frontend/src/components/CitationCard.tsx` |
| CI/CD Pipelines | ✅ Complete | `.github/workflows/` |
| Docker Compose | ✅ Complete | `docker-compose.yml` |
| Evaluation Dataset | ✅ Partial (30 queries) | `data/test-queries/evaluation_dataset.csv` |
| Unit Tests | ✅ Skeleton | `backend/tests/` |

### 2.2 What's NOT Built Yet ⏳

| Component | Status | Notes |
|-----------|--------|-------|
| PostgreSQL + pgvector Integration | ⏳ Schema ready | Using SQLite demo mode currently |
| Redis Caching Layer | ⏳ Planned | `REDIS_URL` in config but not implemented |
| Rate Limiting Middleware | ⏳ Planned | `slowapi` in requirements but not wired in |
| Streaming Chat Endpoint | ⏳ Partial | `/api/chat/stream` endpoint exists but needs testing |
| Admin Dashboard | ⏳ Planned | Frontend pages needed |
| Load Testing | ⏳ Planned | Locust scripts needed |
| Evaluation Framework | ⏳ Partial | Dataset started, testing scripts needed |
| 200-Query Test Dataset | ⏳ Partial | ~30 queries written, need 170 more |
| Full Sentence Transformers Support | ⏳ Deferred | Too heavy for current setup, using OpenAI embeddings |

---

## 3. Architecture

### 3.1 System Architecture (Layered)

```
┌─────────────────────────────────────────────────────────────┐
│                     Client Layer (Next.js)                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │ Chat Input   │  │ Chat History │  │ Citation Display │   │
│  └──────────────┘  └──────────────┘  └──────────────────┘   │
└─────────────────────────┬───────────────────────────────────┘
                          │ HTTP/REST
┌─────────────────────────▼───────────────────────────────────┐
│                     API Layer (FastAPI)                      │
│  ┌────────────┐  ┌──────────────┐  ┌──────────────────┐     │
│  │ /api/chat  │  │ /api/docs    │  │ /api/health      │     │
│  └────────────┘  └──────────────┘  └──────────────────┘     │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                  Processing Layer (Services)                 │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │ Roman Urdu  │  │   Hybrid     │  │   LLM Provider   │   │
│  │ Processing  │  │  Retrieval   │  │   (3-tier)       │   │
│  └─────────────┘  └──────────────┘  └──────────────────┘   │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                     Data Layer (SQLite/PgSQL)               │
│  ┌─────────────┐  ┌──────────────┐                         │
│  │  Documents  │  │    Chunks    │  (embeddings as JSON)   │
│  └─────────────┘  └──────────────┘                         │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Data Flow

```
User Query → Language Detection → Roman Urdu Normalization →
Hybrid Retrieval (Keyword + Semantic) → RRF Fusion →
Context Assembly → LLM Generation → Citation Grounding →
Response + Citations → Frontend Display
```

### 3.3 Request Lifecycle

1. **User types query** → Frontend sends POST to `/api/chat`
2. **Language detection** → `LanguageDetector.detect(query)` → 'en' | 'ur' | 'mixed'
3. **Normalization** → If Roman Urdu, `RomanUrduNormalizer.normalize(query)`
4. **Retrieval** → `HybridRetriever.retrieve()` returns top-K chunks with scores
5. **Prompt assembly** → `RAGPromptBuilder.build()` creates context + system prompt
6. **LLM generation** → `LLMProvider.generate()` with fallback chain
7. **Response formatting** → Citations extracted and attached
8. **Logging** → Query logged to `QueryLog` table
9. **Return** → JSON response to frontend

---

## 4. Tech Stack

### 4.1 Production Stack (as designed)

| Layer | Technology | Version | Purpose |
|-------|------------|---------|---------|
| Frontend | Next.js | 14.1.0 | SSR web application |
| Frontend Language | TypeScript | 5.3.3 | Type safety |
| Frontend Styling | TailwindCSS | 3.4.1 | Utility-first CSS |
| Backend Framework | FastAPI | 0.135.3 | Async REST API |
| Backend Language | Python | 3.12.3 | Backend logic |
| Database | PostgreSQL | 15+ (pgvector) | Vector + relational storage |
| Embeddings | multilingual-e5-large | (deferred) | Multilingual semantic search |
| LLM Primary | Anthropic Claude | API | Response generation |
| LLM Fallback 1 | OpenAI GPT-3.5-turbo | API | Fallback provider |
| LLM Fallback 2 | Ollama + Llama-3-8B | Local | Zero-cost offline fallback |
| Document Processing | PyMuPDF | 1.27.2 | PDF text extraction |
| Caching | Redis | 7.x | Query cache + rate limiting |
| Monitoring | Sentry | Latest | Error tracking |
| Deployment | Vercel + Railway | - | Frontend + Backend hosting |

### 4.2 Current Development Stack (as built)

| Layer | Technology | Notes |
|-------|------------|-------|
| Frontend | Next.js 14 | ✅ Running on :3000 |
| Backend | FastAPI | ✅ Running on :8000 |
| Database | **SQLite** (demo mode) | PostgreSQL not available on dev machine |
| Embeddings | **OpenAI text-embedding-3-small** | Using OpenAI instead of local model |
| LLM | **Anthropic/ OpenAI API** | Requires API keys in `.env` |
| Local ML Models | **Deferred** | Too resource-heavy for dev machine |

### 4.3 Key Dependency Changes from Plan

| Planned | Actual | Reason |
|---------|--------|--------|
| `sentence-transformers` (local) | OpenAI API embeddings | Local model too heavy, download timeout |
| `fasttext` for language detection | Custom rule-based detection | `fasttext` binary compilation issues |
| `pgvector` for embeddings | JSON-serialized embeddings in SQLite | SQLite demo mode |
| PostgreSQL required | SQLite fallback added | PostgreSQL not installed on dev machine |

---

## 5. Folder Structure

```
FYP/
├── .github/
│   └── workflows/
│       ├── backend-ci.yml          # Backend lint + test pipeline
│       ├── frontend-ci.yml         # Frontend lint + build pipeline
│       ├── qwen-dispatch.yml       # (auto-generated)
│       ├── qwen-invoke.yml         # (auto-generated)
│       ├── qwen-review.yml         # (auto-generated)
│       ├── qwen-scheduled-triage.yml # (auto-generated)
│       └── qwen-triage.yml         # (auto-generated)
├── .gitignore
│
├── backend/
│   ├── .env                        # ⚠️ Git-ignored! Local secrets
│   ├── .env.example                # Template for .env
│   ├── Dockerfile                  # Backend container image
│   ├── main.py                     # Uvicorn entry point
│   ├── pyproject.toml              # Python project config + linting rules
│   ├── requirements.txt            # Python dependencies
│   ├── venv/                       # ⚠️ Git-ignored! Virtual environment
│   │
│   ├── app/
│   │   ├── __init__.py             # FastAPI app factory + CORS + Sentry setup
│   │   │
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── chat.py             # POST /api/chat, POST /api/chat/stream, GET /api/chat/suggestions
│   │   │   ├── documents.py        # CRUD /api/documents, upload, reindex, stats
│   │   │   └── health.py           # GET /api/health, /api/health/db, /api/health/llm, /api/health/query-stats
│   │   │
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py           # Pydantic Settings (env-based config)
│   │   │   └── database.py         # SQLAlchemy engine + session (SQLite fallback)
│   │   │
│   │   ├── models/
│   │   │   └── __init__.py         # SQLAlchemy models (Document, Chunk, QueryLog)
│   │   │
│   │   └── services/
│   │       ├── retrieval/
│   │       │   ├── __init__.py
│   │       │   ├── pdf_processor.py    # PyMuPDF PDF extraction + section detection
│   │       │   ├── chunking.py         # Hybrid chunking (section-based + fixed-size)
│   │       │   ├── embeddings.py       # OpenAI embedding generation
│   │       │   └── hybrid_retriever.py # BM25 + vector search + RRF fusion
│   │       │
│   │       ├── roman_urdu/
│   │       │   ├── __init__.py
│   │       │   ├── language_detection.py  # Rule-based English/Roman Urdu/mixed detection
│   │       │   └── normalization.py       # Spelling normalization + dictionary mapping
│   │       │
│   │       └── rag/
│   │           ├── __init__.py
│   │           ├── llm_provider.py   # 3-tier LLM provider with circuit breaker
│   │           └── prompt.py         # RAG prompt builder + citation system
│   │
│   └── tests/
│       ├── __init__.py
│       ├── test_language_detection.py
│       ├── test_normalization.py
│       └── test_chunking.py
│
├── frontend/
│   ├── Dockerfile                  # Frontend container image
│   ├── next.config.js              # Next.js configuration
│   ├── next-env.d.ts               # TypeScript declarations
│   ├── package.json                # Node.js dependencies
│   ├── package-lock.json           # Dependency lock file
│   ├── postcss.config.js           # PostCSS configuration
│   ├── tailwind.config.js          # TailwindCSS configuration
│   ├── tsconfig.json               # TypeScript configuration
│   ├── node_modules/               # ⚠️ Git-ignored!
│   │
│   └── src/
│       ├── app/
│       │   ├── layout.tsx          # Root layout with metadata
│       │   ├── page.tsx            # Main chat page (client component)
│       │   └── globals.css         # Global styles + animations
│       │
│       ├── components/
│       │   ├── ChatMessage.tsx     # Message bubble with citations
│       │   ├── ChatInput.tsx       # Textarea with auto-resize
│       │   ├── CitationCard.tsx    # Expandable citation source
│       │   └── TypingIndicator.tsx  # Animated typing dots
│       │
│       └── lib/
│           └── api.ts              # Typed API client (ApiClient class)
│
├── data/
│   ├── raw/                        # Place PDFs here for ingestion
│   ├── processed/                  # Cleaned text output
│   └── test-queries/
│       └── evaluation_dataset.csv  # Test queries (30/200 complete)
│
├── docs/
│   └── IMPLEMENTATION_PLAN.md      # 20-week phased implementation plan
│
├── logs/
│   ├── backend.log                 # Backend server output
│   └── frontend.log                # Frontend server output
│
├── scripts/
│   ├── init_db.py                  # Database initialization script
│   └── ingest_documents.py         # PDF ingestion CLI script
│
├── docker-compose.yml              # Full stack Docker configuration
├── README.md                       # Project README
├── FINAL YEAR PROJECT PROPOSAL.md  # Original project proposal
└── CONTEXT.md                      # ← This file
```

---

## 6. Database Schema

### 6.1 Current (SQLite-compatible)

```sql
-- Documents table
CREATE TABLE documents (
    id VARCHAR(36) PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    year INTEGER,
    source_path VARCHAR(500),
    ingested_at DATETIME
);

-- Chunks table (embeddings stored as JSON strings)
CREATE TABLE chunks (
    id VARCHAR(36) PRIMARY KEY,
    doc_id VARCHAR(36) NOT NULL REFERENCES documents(id),
    content TEXT NOT NULL,
    embedding_data TEXT,        -- JSON array of floats
    section_header VARCHAR(300),
    page_start INTEGER,
    page_end INTEGER,
    chunk_type VARCHAR(50),     -- 'text', 'table', 'list'
    chunk_order INTEGER,
    created_at DATETIME
);

-- Query logs for analytics
CREATE TABLE query_logs (
    id VARCHAR(36) PRIMARY KEY,
    query_text TEXT NOT NULL,
    detected_language VARCHAR(20),
    normalized_query TEXT,
    response TEXT,
    latency_ms INTEGER,
    cache_hit BOOLEAN DEFAULT FALSE,
    llm_provider VARCHAR(50),
    retrieval_scores TEXT,      -- JSON string
    created_at DATETIME
);
CREATE INDEX ix_query_logs_created_at ON query_logs (created_at);
```

### 6.2 Production (PostgreSQL with pgvector)

```sql
-- Same schema but with:
-- - UUID type for IDs (instead of VARCHAR(36))
-- - vector(1024) type for embedding column (instead of TEXT JSON)
-- - GIN index for full-text search: CREATE INDEX chunks_content_idx ON chunks USING GIN (to_tsvector('english', content));
-- - IVFFlat index for vector search: CREATE INDEX chunks_embedding_idx ON chunks USING ivfflat (embedding vector_cosine_ops);
```

---

## 7. API Endpoints

### 7.1 Chat

```
POST /api/chat
Body: {
  "query": "What documents are required for admission?",
  "top_k": 10,          // optional, default 10
  "use_hybrid": true,   // optional, default true
  "stream": false       // optional, default false
}
Response: {
  "response": "...",
  "citations": [...],
  "latency_ms": 1234,
  "llm_provider": "anthropic",
  "cache_hit": false,
  "language": "en"
}
```

### 7.2 Documents

```
GET    /api/documents                  # List all documents
POST   /api/documents/upload           # Upload PDF (multipart/form-data)
GET    /api/documents/{id}             # Get document details
DELETE /api/documents/{id}             # Delete document
POST   /api/documents/{id}/reindex     # Re-index document
GET    /api/documents/stats            # Get statistics
```

### 7.3 Health

```
GET    /api/health                     # Overall health
GET    /api/health/db                  # Database health
GET    /api/health/llm                 # LLM provider health
GET    /api/health/query-stats?hours=24 # Query analytics
```

### 7.4 Chat Extras

```
POST   /api/chat/stream                # Server-Sent Events streaming
GET    /api/chat/suggestions?limit=5   # Get suggested queries
```

---

## 8. Configuration

### 8.1 Environment Variables (`backend/.env`)

```bash
# Required
DATABASE_URL="postgresql://..."     # or auto-detects SQLite mode
OPENAI_API_KEY="sk-..."             # For embeddings + LLM fallback

# Optional
ANTHROPIC_API_KEY=""                # Primary LLM provider
OLLAMA_BASE_URL="http://localhost:11434"
SENTRY_DSN=""

# Tunable
LLM_TEMPERATURE=0.3
LLM_MAX_TOKENS=1024
RETRIEVAL_TOP_K=20
RRF_K=60
RRF_WEIGHT_KEYWORD=0.5
RRF_WEIGHT_SEMANTIC=0.5
RATE_LIMIT_PER_MINUTE=10
RATE_LIMIT_PER_HOUR=100
```

### 8.2 Frontend Environment

```bash
# Set at build time or in next.config.js
API_URL="http://localhost:8000"    # Backend URL
```

---

## 9. Development Conventions

### 9.1 Backend (Python)

- **Code Style:** Ruff linter (configured in `pyproject.toml`)
- **Line Length:** 100 characters
- **Type Hints:** Encouraged, not enforced
- **Imports:** Absolute from `app.` namespace
- **Error Handling:** Try/except with structured error responses
- **Testing:** Pytest in `backend/tests/` directory

### 9.2 Frontend (TypeScript/React)

- **Code Style:** ESLint + Next.js defaults
- **Components:** Functional components with `'use client'` directive
- **Styling:** TailwindCSS utility classes (no CSS modules)
- **Type Safety:** Interfaces for all API types in `lib/api.ts`
- **File Naming:** PascalCase for components, camelCase for utilities

### 9.3 Git

- **Branch Naming:** `feature/description`, `fix/description`
- **Commit Style:** Conventional commits (`feat:`, `fix:`, `docs:`, `chore:`)
- **Current Branch:** `initial-prototype`

---

## 10. Constraints & Limitations

### 10.1 Current Constraints

| Constraint | Impact | Workaround |
|------------|--------|------------|
| No PostgreSQL on dev machine | Using SQLite demo | Embeddings stored as JSON, no vector search optimization |
| No GPU available | Can't run local embedding models | Using OpenAI API for embeddings |
| No API keys configured | LLM responses will fail | System falls back to error message with retrieved chunks |
| Only 30 test queries | Evaluation incomplete | Need 170 more queries for target of 200 |

### 10.2 Design Constraints (from Proposal)

| Constraint | Details |
|------------|---------|
| No admission prediction | Cannot predict merit or ranking |
| No application processing | Informational only, not a workflow system |
| No personal data storage | GDPR compliant, no user tracking |
| Citation required | All factual claims must cite sources |
| Document-based only | Cannot use web search or outside knowledge |

---

## 11. How to Work With This Project

### 11.1 Starting Services

```bash
# Backend (from project root)
cd backend && source venv/bin/activate && uvicorn main:app --reload

# Frontend (from project root)
cd frontend && npm run dev
```

### 11.2 Adding Admission Documents

```bash
# Place PDFs in data/raw/
cp path/to/prospectus.pdf data/raw/

# Run ingestion
cd backend && source venv/bin/activate
python ../scripts/ingest_documents.py ../data/raw/prospectus.pdf
```

### 11.3 Running Tests

```bash
cd backend && source venv/bin/activate
pytest tests/ -v
```

### 11.4 Building for Production

```bash
# Frontend
cd frontend && npm run build

# Backend
# Deploy with Docker Compose or Railway
```

---

## 12. Key Files to Know

| File | Purpose |
|------|---------|
| `backend/.env` | **Secrets** — DO NOT COMMIT |
| `backend/app/__init__.py` | App factory — add middleware here |
| `backend/app/core/config.py` | All configuration loaded from env |
| `backend/app/models/__init__.py` | Database schema definition |
| `backend/app/api/chat.py` | Main chat endpoint logic |
| `frontend/src/app/page.tsx` | Main chat UI |
| `frontend/src/lib/api.ts` | API client — single source of truth for API types |
| `scripts/ingest_documents.py` | CLI for adding PDFs to the system |
| `docker-compose.yml` | Full stack deployment configuration |

---

## 13. Running Processes

| Process | PID | URL |
|---------|-----|-----|
| Backend | 136168 | http://localhost:8000 |
| Frontend | 136247 | http://localhost:3000 |

---

## 14. Next Steps for Continuation

1. **Add API keys** to `backend/.env` (OpenAI or Anthropic)
2. **Ingest admission PDFs** using `scripts/ingest_documents.py`
3. **Test the chatbot** at http://localhost:3000
4. **Complete evaluation dataset** — add 170 more test queries
5. **Implement Redis caching** for performance
6. **Add rate limiting middleware** with slowapi
7. **Set up PostgreSQL** for production deployment
8. **Add more unit tests** for retrieval and RAG components
9. **Create admin dashboard** for document management
10. **Write final thesis document**
