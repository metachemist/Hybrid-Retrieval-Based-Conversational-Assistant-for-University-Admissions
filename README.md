# Admission Policy Chatbot

A hybrid retrieval-based conversational assistant for University of Karachi admission policies.

## Overview

This project implements a **Retrieval-Augmented Generation (RAG)** system that helps prospective students understand admission policies through natural language queries in **English** and **Roman Urdu**.

### Key Features

- **Hybrid Retrieval**: Combines keyword search (BM25) with semantic vector search using Reciprocal Rank Fusion (RRF)
- **Multilingual Support**: Handles English, Roman Urdu, and code-mixed query
- **Citation-Grounded Responses**: All answers include citations to source documents
- **LLM Fallback Chain**: Automatic failover — Gemini → Anthropic → OpenAI → Ollama
- **Authentication**: User login, registration, and forgot/reset password flows
- **Admin Panel**: Document management and ingestion interface
- **Caching & Rate Limiting**: Redis-backed caching with per-minute/per-hour rate limits
- **Monitoring**: Sentry integration for error tracking

## Tech Stack

| Component | Technology |
|-----------|------------|
| Frontend | Next.js 14 + TypeScript + TailwindCSS |
| Backend | FastAPI (Python 3.11+) |
| Database | Neon PostgreSQL + pgvector |
| Migrations | Alembic |
| Embeddings | multilingual-e5-large (prod) / text-embedding-3-small (dev) |
| LLM | Google Gemini (primary) / Anthropic Claude / OpenAI GPT / Ollama |
| Document Processing | PyMuPDF |
| Caching | Redis |

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- PostgreSQL 15+ with pgvector extension
- Redis
- At least one LLM API key (Gemini recommended — free tier)

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
# Edit .env — set DATABASE_URL and at least one LLM API key

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

Visit `http://localhost:3000` to access the chatbot.

## Environment Variables

Key variables in `backend/.env`:

```env
# Database (Neon PostgreSQL)
DATABASE_URL="postgresql://user:password@host/admission_db"

# LLM Provider Keys (set at least one; Gemini is free-tier)
GEMINI_API_KEY=""
ANTHROPIC_API_KEY=""
OPENAI_API_KEY=""

# Embedding Model
EMBEDDING_MODEL="text-embedding-3-small"   # dev
# EMBEDDING_MODEL="intfloat/multilingual-e5-large"  # prod

# Redis
REDIS_URL="redis://localhost:6379"

# Auth
SECRET_KEY="change-me-in-production"
ADMIN_REGISTRATION_KEY="your-strong-admin-key"

# Rate Limiting
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
cd backend
ruff check app/

cd frontend
npm run lint
```

## Deployment

| Service | Platform |
|---------|----------|
| Frontend | Vercel |
| Backend | Railway |
| Database | Neon |

Set `API_URL` in the Vercel environment to point to your Railway backend.

## License

This project is part of a Final Year Project at the University of Karachi.
