# Rehnuma

Rehnuma is a hybrid retrieval-based conversational assistant for University of Karachi
admission policies. It answers natural-language questions in **English** and **Roman Urdu**,
and every answer is grounded in — and cited back to — the official admission documents.

Final Year Project, University of Karachi. Live deployment: Vercel (frontend) + Render
(backend) + Neon (database).

## How it works

1. The query language is detected (English / Roman Urdu / code-mixed). Roman Urdu and
   code-mixed queries are spelling-normalised before retrieval — the query is never
   machine-translated to English first.
2. **Hybrid retrieval** runs two searches over the chunked documents and fuses them with
   Reciprocal Rank Fusion (RRF):
   - PostgreSQL full-text search over a generated `tsvector` column (GIN-indexed), and
   - semantic search over `gemini-embedding-001` vectors (pgvector, HNSW cosine index).
   Count / "list all" questions take a wider recall-oriented path instead of top-k.
3. The top chunks are assembled into a RAG prompt and sent to the LLM. Answers carry
   inline `[1] [2]` markers that map to the retrieved sources.
4. Responses stream to the client over Server-Sent Events. Completed answers are cached in
   Redis (when configured) and every query is logged for the analytics dashboard.

## Features

- **Hybrid retrieval** — BM25-style keyword search + semantic vector search, fused with RRF
- **Multilingual** — English, Roman Urdu and code-mixed queries; answered in the language asked
- **Citation-grounded answers** — every factual claim links to a document, section and page
- **Streaming** — token-by-token responses over SSE, with a non-streaming `/api/chat` fallback
- **LLM provider chain** — Google Gemini primary (free tier), optional OpenAI fallback, with a
  per-provider circuit breaker
- **Auth** — registration, login, and forgot / reset password (JWT, bcrypt)
- **Admin dashboard** — document upload / reindex / delete, plus usage analytics
- **Caching & rate limiting** — optional Redis response cache; per-IP rate limits on chat and auth
- **Monitoring** — optional Sentry error tracking

## Tech stack

| Component | Technology |
|-----------|------------|
| Frontend | Next.js 14, TypeScript, Tailwind CSS |
| Backend | FastAPI (Python 3.11+) |
| Database | PostgreSQL + pgvector (Neon) |
| Migrations | Alembic |
| Embeddings | Google `gemini-embedding-001` (768-dim, L2-normalised) |
| Generation | Google Gemini (primary) · OpenAI GPT (optional fallback) |
| Document parsing | PyMuPDF; OpenAI vision for image-only notices (ingestion only) |
| Cache / rate limiting | Redis (optional) · slowapi |

## Quick start

### Prerequisites

- Python 3.11+
- Node.js 20+
- PostgreSQL 15+ with the `pgvector` extension
- A Google Gemini API key ([aistudio.google.com/apikey](https://aistudio.google.com/apikey)) —
  powers both embeddings and answer generation
- Optional: Redis (response cache), an OpenAI key (generation fallback + image ingestion)

`docker compose up postgres redis` brings up Postgres + Redis locally.

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate            # venv\Scripts\activate on Windows
pip install -r requirements.txt

cp .env.example .env                # then set DATABASE_URL and GEMINI_API_KEY

alembic upgrade head
uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local   # points NEXT_PUBLIC_API_URL at localhost:8000
npm run dev
```

Open <http://localhost:3000>.

### Ingesting documents

The database ships already populated. To load documents into a fresh database:

```bash
python scripts/init_db.py                       # enable pgvector, create tables
python scripts/ingest_documents.py <path>       # a PDF/image file, or a directory of them
```

## Environment variables

Set these in `backend/.env` (see `.env.example` for the complete list):

```env
DATABASE_URL="postgresql://user:password@host/dbname?sslmode=require"

GEMINI_API_KEY=""                  # required — embeddings + generation
GEMINI_MODEL="gemini-3.6-flash"    # Google rotates model ids; set to whatever is current
OPENAI_API_KEY=""                  # optional — generation fallback + image transcription
OPENAI_MODEL="gpt-4o"             # only used when OPENAI_API_KEY is set

EMBEDDING_MODEL="gemini-embedding-001"
EMBEDDING_DIMENSION=768            # keep in sync with the models + alembic migrations

REDIS_URL="redis://localhost:6379"  # blank disables the response cache

# The app refuses to start with these placeholders unless DEBUG=true.
# Generate: python -c "import secrets; print(secrets.token_urlsafe(48))"
SECRET_KEY="change-me-in-production"
ADMIN_REGISTRATION_KEY="your-strong-admin-key"

CORS_ORIGINS=["http://localhost:3000"]   # JSON list; add the deployed frontend origin
```

Frontend: `frontend/.env.local` needs `NEXT_PUBLIC_API_URL` (the backend base URL).

## API

| Method | Path | Notes |
|--------|------|-------|
| `POST` | `/api/chat` | RAG answer as JSON (`query`, `top_k`, `use_hybrid`) |
| `POST` | `/api/chat/stream` | Same, streamed as SSE (`meta` / `token` / `done` / `error` events) |
| `POST` | `/api/auth/register` · `/api/auth/login` | JWT; `admin_key` on register grants the admin role |
| `GET`  | `/api/auth/me` | Current user profile |
| `POST` | `/api/auth/forgot-password` · `/api/auth/reset-password` | Token-based reset |
| `GET`  | `/api/documents` · `/api/documents/{id}` · `/api/documents/stats` | Public reads |
| `POST` | `/api/documents/upload` · `/api/documents/{id}/reindex` | Admin only |
| `DELETE` | `/api/documents/{id}` | Admin only |
| `GET`  | `/api/admin/analytics/{overview,queries,languages,topics,performance,top-queries}` | Admin only |
| `GET`  | `/api/admin/users` | Admin only |
| `GET`  | `/api/health` · `/api/health/db` · `/api/health/llm` | Status checks |

## Project structure

```
.
├── backend/
│   ├── app/
│   │   ├── api/               # FastAPI routes: auth, admin, chat, documents, health
│   │   ├── core/              # config, database, cache, ratelimit, security
│   │   ├── models/            # SQLAlchemy models (Document, Chunk, QueryLog, User)
│   │   └── services/
│   │       ├── analytics/     # keyword topic classifier
│   │       ├── rag/           # LLM provider chain + RAG prompt builder
│   │       ├── retrieval/     # hybrid retriever, embeddings, PDF/image parsing, chunking
│   │       └── roman_urdu/    # language detection + spelling normalisation
│   ├── alembic/               # database migrations
│   └── tests/                 # pytest (chunking, language detection, normalisation, topics)
├── frontend/
│   └── src/
│       ├── app/               # Next.js routes: landing, chat, login, register,
│       │                      #   forgot/reset-password, admin, admin/documents
│       ├── components/        # chat UI, citation cards, admin charts, landing visuals
│       └── lib/               # API client, auth context, formatting helpers
├── scripts/
│   ├── init_db.py             # create tables + enable pgvector
│   ├── ingest_documents.py    # parse, chunk, embed and store a document or directory
│   ├── reembed_chunks.py      # re-embed all chunks after an embedding-model change
│   └── evaluate.py            # retrieval + generation benchmark against the eval set
├── data/test-queries/         # evaluation dataset + last results
├── docs/                      # implementation plan, thesis report
├── .github/workflows/         # backend-ci, frontend-ci
└── docker-compose.yml         # local Postgres + Redis (+ optional full stack)
```

> Source documents are ingested into the database and are **not** tracked in this repo
> (`FYP DOCUMENTS/`, `data/raw/` and `backend/data/` are git-ignored).

## Development

```bash
cd backend && pytest -q                    # backend tests
cd backend && pip install ruff && ruff check app/   # backend lint (ruff not in requirements)
cd frontend && npm run lint                # frontend lint
cd frontend && npx tsc --noEmit            # frontend type-check
```

## Evaluation

`python scripts/evaluate.py` scores keyword-only, semantic-only and hybrid retrieval
(Recall@5/@10, MRR) plus the full generation pipeline (citation validity, latency, and an
LLM-judge groundedness proxy) against `data/test-queries/evaluation_dataset.csv`.

| Metric | Target |
|--------|--------|
| Retrieval Recall@5 | > 80% |
| Answer correctness (human) | > 75% |
| Citation accuracy | > 90% |
| Response time | < 3 s |
| Roman Urdu success | > 70% |

Measured figures are reported in `docs/THESIS_REPORT.md`.

## Deployment

| Service | Platform |
|---------|----------|
| Frontend | Vercel |
| Backend | Render (Docker web service) |
| Database | Neon (PostgreSQL + pgvector) |

- Migrations run automatically on each backend deploy (`alembic upgrade head` in the
  Docker `CMD`).
- On Render, set `DATABASE_URL`, `GEMINI_API_KEY`, `SECRET_KEY`, `ADMIN_REGISTRATION_KEY`
  and `CORS_ORIGINS` (include the exact Vercel origin, no trailing slash). Leave `DEBUG`
  unset. `OPENAI_API_KEY` and `REDIS_URL` are optional.
- Set `NEXT_PUBLIC_API_URL` in the Vercel project to the Render backend URL.

> Free-tier Render instances spin down when idle; the first request after a cold start can
> take a minute. The free tier's filesystem is also ephemeral — PDFs uploaded through the
> admin panel are lost on redeploy (which breaks `reindex`); point `UPLOAD_DIR` at a
> mounted disk or object storage for durable uploads.

## License

Part of a Final Year Project at the University of Karachi.
