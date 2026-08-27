# Rehnuma

Rehnuma is a hybrid retrieval-based conversational assistant for University of Karachi admission policies.

## Overview

This project implements a **Retrieval-Augmented Generation (RAG)** system that helps prospective students understand admission policies through natural language queries in **English** and **Roman Urdu**.

### Key Features

- **Hybrid Retrieval**: Combines keyword search (BM25) with semantic vector search using Reciprocal Rank Fusion (RRF)
- **Multilingual Support**: Handles English, Roman Urdu, and code-mixed query
- **Citation-Grounded Responses**: All answers include citations to source documents
- **LLM Provider Chain**: Google Gemini (primary, free tier) with optional failover to OpenAI, plus a per-provider circuit breaker
- **Authentication**: User login, registration, and forgot/reset password flows
- **Admin Panel**: Document management and ingestion interface
- **Caching & Rate Limiting**: optional Redis response cache; per-IP per-minute/per-hour rate limits on the chat and auth endpoints
- **Monitoring**: Sentry integration for error tracking

## Tech Stack

| Component | Technology |
|-----------|------------|
| Frontend | Next.js 14 + TypeScript + TailwindCSS |
| Backend | FastAPI (Python 3.11+) |
| Database | Neon PostgreSQL + pgvector |
| Migrations | Alembic |
| Embeddings | Google gemini-embedding-001 (768-dim) |
| LLM | Google Gemini (primary) / OpenAI GPT (optional fallback) |
| Document Processing | PyMuPDF |
| Caching | Redis (optional) |

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- PostgreSQL 15+ with pgvector extension
- Redis (optional — enables the response cache; the app runs without it)
- A Google Gemini API key (required — powers embeddings + answer generation); an OpenAI key is an optional generation fallback

The fastest way to get Postgres + Redis locally is `docker compose up postgres redis`.

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
# Edit .env: set DATABASE_URL and at least one LLM API key

# Run database migrations
alembic upgrade head

# Start server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Visit `http://localhost:3000` to access Rehnuma.

## Environment Variables

Key variables in `backend/.env`:

```env
# Database (Neon PostgreSQL)
DATABASE_URL="postgresql://user:password@host/admission_db"

# LLM Provider Keys — Gemini is required, OpenAI is an optional generation fallback
GEMINI_API_KEY=""
OPENAI_API_KEY=""
GEMINI_MODEL="gemini-3.6-flash"   # Google rotates these; set to whatever is current
OPENAI_MODEL="gpt-4o"            # only used when OPENAI_API_KEY is set

# Embedding Model (Google gemini-embedding-001, 768-dim)
EMBEDDING_MODEL="gemini-embedding-001"
EMBEDDING_DIMENSION=768

# Redis — leave blank to disable the response cache
REDIS_URL="redis://localhost:6379"

# Auth — the app refuses to start with these placeholders unless DEBUG=true.
# Generate: python -c "import secrets; print(secrets.token_urlsafe(48))"
SECRET_KEY="change-me-in-production"
ADMIN_REGISTRATION_KEY="your-strong-admin-key"

# Rate Limiting (per client IP, applied to /api/chat* and /api/auth/{login,register})
RATE_LIMIT_PER_MINUTE=10
RATE_LIMIT_PER_HOUR=100
```

See `.env.example` for the full list.

## Project Structure

```
.
├── backend/
│   ├── app/
│   │   ├── api/              # FastAPI routes (chat, documents, auth, admin, health)
│   │   ├── core/             # Config, database
│   │   ├── models/           # SQLAlchemy models
│   │   └── services/
│   │       ├── analytics/    # Usage analytics
│   │       ├── rag/          # LLM provider + prompt templates
│   │       ├── retrieval/    # Hybrid search engine + embeddings
│   │       └── roman_urdu/   # Language detection + normalization
│   ├── alembic/              # Database migrations
│   ├── tests/
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── app/              # Next.js pages (chat, login, register, admin, ...)
│       ├── components/       # ChatInput, ChatMessage, CitationCard, ...
│       └── lib/              # API client
├── data/
│   ├── raw/                  # Original PDFs
│   └── processed/            # Cleaned text
├── scripts/
│   └── ingest_documents.py   # Ingestion pipeline
└── docker-compose.yml
```

## API Endpoints

### Chat

```bash
POST /api/chat
{
  "query": "What documents are required for admission?",
  "top_k": 10,
  "use_hybrid": true
}
```

### Documents

```bash
GET    /api/documents
POST   /api/documents/upload     # multipart/form-data: file + title
DELETE /api/documents/{id}
```

### Auth

```bash
POST /api/auth/register
POST /api/auth/login
POST /api/auth/forgot-password
POST /api/auth/reset-password
```

### Health

```bash
GET /api/health
GET /api/health/db
GET /api/health/llm
```

## Roman Urdu Support

The system includes a custom Roman Urdu processing module:

```python
from app.services.roman_urdu import LanguageDetector, RomanUrduNormalizer

detector = LanguageDetector()
normalizer = RomanUrduNormalizer()

lang, confidence = detector.detect("admission ke liye kya documents chahiye?")
# ('ur', 0.85) or ('mixed', 0.72)

normalized = normalizer.normalize("kal mein admission ke liye apply kaise karein?")
```

## Evaluation Targets

| Metric | Target |
|--------|--------|
| Retrieval Recall@5 | >80% |
| Answer Correctness | >75% |
| Citation Accuracy | >90% |
| Response Time | <3s |
| Roman Urdu Success | >70% |

## Development

### Tests

```bash
cd backend
pytest tests/ -v
```

### Linting

```bash
# backend (ruff is not in requirements.txt; install it first)
cd backend && pip install ruff && ruff check app/

# frontend
cd frontend && npm run lint
```

## Deployment

| Service | Platform |
|---------|----------|
| Frontend | Vercel |
| Backend | Render |
| Database | Neon |

Backend is deployed on Render (Docker web service) at `https://university-admissions-chatbot.onrender.com`. Railway was tried first but hit deployment errors. Set `NEXT_PUBLIC_API_URL` in the Vercel environment to point to the Render backend.

On Render, set `SECRET_KEY`, `ADMIN_REGISTRATION_KEY`, `GEMINI_API_KEY` (and optionally `OPENAI_API_KEY`, `REDIS_URL`) as environment variables. Leave `DEBUG` unset/false — the backend refuses to start with placeholder auth secrets when `DEBUG` is off.

> Free-tier Render instances spin down after inactivity; the first request after idling can take 50+ seconds to respond.
>
> Render's free tier has an ephemeral filesystem: PDFs uploaded through the admin panel are lost on redeploy, which also breaks `POST /api/documents/{id}/reindex`. Point `UPLOAD_DIR` at a mounted disk (or use object storage) for durable uploads.

## License

This project is part of a Final Year Project at the University of Karachi.
