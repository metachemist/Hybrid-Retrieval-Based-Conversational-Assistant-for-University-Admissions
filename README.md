# Admission Policy Chatbot

A hybrid retrieval-based conversational assistant for University of Karachi admission policies.

## Overview

This project implements a **Retrieval-Augmented Generation (RAG)** system that helps prospective students understand admission policies through natural language queries in **English** and **Roman Urdu**.

### Key Features

- 📚 **Hybrid Retrieval**: Combines keyword search (BM25) with semantic vector search using Reciprocal Rank Fusion (RRF)
- 🌐 **Multilingual Support**: Handles English, Roman Urdu, and code-mixed queries
- 📝 **Citation-Grounded Responses**: All answers include citations to source documents
- 🤖 **LLM Fallback**: Automatic failover between Anthropic → OpenAI → Local Ollama
- ⚡ **Fast Response**: Caching and optimized retrieval for sub-3-second responses

## Tech Stack

| Component | Technology |
|-----------|------------|
| Frontend | Next.js 14 + TypeScript + TailwindCSS |
| Backend | FastAPI (Python 3.11+) |
| Database | Neon PostgreSQL + pgvector |
| Embeddings | multilingual-e5-large |
| LLM | Anthropic Claude / OpenAI GPT / Ollama |
| Document Processing | PyMuPDF |

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- PostgreSQL 15+ with pgvector extension
- API keys for LLM provider (Anthropic/OpenAI)

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

# Edit .env with your settings
# - DATABASE_URL
# - ANTHROPIC_API_KEY or OPENAI_API_KEY

# Initialize database
python ../scripts/init_db.py

# Start server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Visit `http://localhost:3000` to access the chatbot.

## Project Structure

```
FYP/
├── backend/
│   ├── app/
│   │   ├── api/              # FastAPI routes
│   │   ├── core/             # Config, database
│   │   ├── models/           # SQLAlchemy models
│   │   └── services/         # Business logic
│   │       ├── retrieval/    # Hybrid search engine
│   │       ├── rag/          # LLM integration
│   │       └── roman_urdu/   # Language processing
│   ├── tests/
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/              # Next.js pages
│   │   ├── components/       # React components
│   │   └── lib/              # API client
│   └── package.json
├── data/
│   ├── raw/                  # Original PDFs
│   └── processed/            # Cleaned text
├── docs/
│   └── IMPLEMENTATION_PLAN.md
├── scripts/
│   └── init_db.py
└── .github/workflows/        # CI/CD pipelines
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
# List documents
GET /api/documents

# Upload document
POST /api/documents/upload
Content-Type: multipart/form-data
file: <pdf_file>
title: "Admission Prospectus 2024"

# Delete document
DELETE /api/documents/{document_id}
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

# Detect language
lang, confidence = detector.detect("admission ke liye kya documents chahiye?")
# Returns: ('ur', 0.85) or ('mixed', 0.72)

# Normalize query
normalized = normalizer.normalize("kal mein admission ke liye apply kaise karein?")
# Returns: normalized query
```

## Evaluation

The system is evaluated on:

| Metric | Target |
|--------|--------|
| Retrieval Recall@5 | >80% |
| Answer Correctness | >75% |
| Citation Accuracy | >90% |
| Response Time | <3s |
| Roman Urdu Success | >70% |

## Development

### Running Tests

```bash
# Backend tests
cd backend
pytest tests/ -v

# Frontend tests
cd frontend
npm test
```

### Linting

```bash
# Backend
cd backend
ruff check app/

# Frontend
cd frontend
npm run lint
```

## Deployment

### Backend (Railway)

```bash
# Set environment variables in Railway dashboard
# Deploy from GitHub repository
```

### Frontend (Vercel)

```bash
# Connect GitHub repository
# Set API_URL environment variable
# Deploy automatically on push
```

### Database (Neon)

```bash
# Create serverless PostgreSQL instance
# Enable pgvector extension
# Copy connection string to backend .env
```

## License

This project is part of a Final Year Project at the University of Karachi.

## Contact

For questions about this project, please contact the development team.

---

**Note:** This chatbot provides information based on official admission documents. Always verify critical information with the University admission office.
