# Revised Implementation Plan: Hybrid RAG-Based Admission Policy Chatbot
*(Gap-Addressed Version)*

**Project:** Design and Implementation of a Hybrid Retrieval-Based Conversational Assistant for University Admission Policies

**University:** University of Karachi

**Supervisor:** Miss Humaira Tariq

**Last Updated:** April 2, 2026

---

## Executive Summary

This document presents a comprehensive 20-week implementation plan for developing a RAG-based conversational assistant that helps prospective students understand University of Karachi admission policies. The system combines hybrid retrieval (keyword + semantic search) with large language models to provide accurate, citation-grounded responses in English and Roman Urdu.

---

## Tech Stack (Finalized)

| Layer | Technology | Rationale |
|-------|------------|-----------|
| Frontend | Next.js 14 + TypeScript + TailwindCSS | SSR support, responsive UI |
| Backend API | FastAPI (Python 3.11+) | Async support, auto OpenAPI docs |
| Database | Neon PostgreSQL + pgvector | Serverless, free tier available |
| Embeddings | `intfloat/multilingual-e5-large` | Strong multilingual + Roman Urdu performance |
| LLM Primary | Anthropic Claude API | Better multilingual support, lower cost than GPT-4 |
| LLM Fallback | OpenAI GPT-3.5-turbo | Widely available, cost-effective |
| Local Fallback | Ollama + Llama-3-8B | Zero-cost offline option |
| Document Processing | PyMuPDF + unstructured | PDF parsing + table extraction |
| Language Detection | fasttext + custom Roman Urdu rules | Better code-mixing handling |
| Rate Limiting | slowapi (Redis-backed) | Configurable, production-ready |
| Monitoring | Sentry + custom logging | Error tracking + query analytics |

---

## Phase 1: Project Setup & Foundation (Weeks 1-2)

### 1.1 Repository Structure

```
FYP/
├── backend/
│   ├── app/
│   │   ├── api/            # API routes
│   │   ├── core/           # Config, security
│   │   ├── models/         # DB models
│   │   ├── services/       # Business logic
│   │   │   ├── retrieval/  # Hybrid search engine
│   │   │   ├── rag/        # LLM integration
│   │   │   └── roman_urdu/ # Normalization module
│   │   └── utils/          # Helpers
│   ├── tests/
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/     # Chat UI, citations
│   │   ├── app/            # Next.js pages
│   │   └── lib/            # API client
│   └── tailwind.config.js
├── data/
│   ├── raw/                # Original PDFs
│   ├── processed/          # Cleaned text
│   └── test-queries/       # Evaluation dataset
├── docs/                   # Thesis, slides
├── scripts/                # Ingestion, evaluation
└── docker-compose.yml      # Local development
```

### 1.2 Infrastructure Setup

- [ ] Initialize Git repository with `.gitignore`
- [ ] Create `README.md` with setup instructions
- [ ] Set up Python virtual environment + dependency management
- [ ] Configure Neon PostgreSQL database (free tier)
- [ ] Enable pgvector extension
- [ ] Set up environment variables template (`.env.example`)

### 1.3 CI/CD Pipeline

- [ ] GitHub Actions for linting (ruff, eslint)
- [ ] Automated testing on PR
- [ ] Deployment workflow (Vercel for frontend, Railway for backend)

---

## Phase 2: Roman Urdu Processing Module (Weeks 3-4) ⭐ *New*

### 2.1 Language Detection

- [ ] Integrate `fasttext` language identification model
- [ ] Train custom classifier for English/Roman Urdu/code-mixed detection
- [ ] Create threshold rules for ambiguous cases

### 2.2 Roman Urdu Normalization

- [ ] Build spelling variation dictionary (crowdsource from students):
  - `kul` → `university`, `admission` → `admission`, `fee` → `fee`
  - Common variations: `kal/kull/kul`, `admisn/admission`, `fii/fee`
- [ ] Implement rule-based normalization:
  - Character mapping (aa→a, ee→e, oo→o)
  - Common suffix/prefix handling
- [ ] Create context-aware correction using edit distance + frequency

### 2.3 Query Preprocessing Pipeline

```
Raw Query → Language Detection → Roman Urdu Normalization → 
Tokenization → Stopword Removal → Normalized Query
```

### 2.4 Evaluation

- [ ] Test on 50 sample Roman Urdu queries
- [ ] Measure normalization accuracy (>85% target)

---

## Phase 3: Document Processing & Knowledge Base (Weeks 5-6)

### 3.1 PDF Ingestion Pipeline

- [ ] PyMuPDF text extraction with page preservation
- [ ] Table extraction using `unstructured` library
- [ ] Image/figure detection (store metadata, skip content)
- [ ] Text cleaning: remove headers/footers, fix line breaks

### 3.2 Chunking Strategy *(Gap Addressed)*

- [ ] **Hybrid approach:**
  - Section-based chunks (respect document structure)
  - Fixed-size fallback (512 tokens with 50 token overlap)
  - Tables kept as single chunks when possible
- [ ] Metadata enrichment:
  - Document ID, title, year
  - Section header, subsection
  - Page numbers
  - Chunk type (text/table/list)

### 3.3 Database Schema *(Gap Addressed)*

```sql
-- Documents table
CREATE TABLE documents (
    id UUID PRIMARY KEY,
    title VARCHAR(500),
    year INTEGER,
    source_path VARCHAR(500),
    ingested_at TIMESTAMP
);

-- Chunks table with pgvector
CREATE TABLE chunks (
    id UUID PRIMARY KEY,
    doc_id UUID REFERENCES documents(id),
    content TEXT,
    embedding vector(1024),  -- multilingual-e5-large dimension
    section_header VARCHAR(300),
    page_start INTEGER,
    page_end INTEGER,
    chunk_type VARCHAR(50),
    chunk_order INTEGER
);

-- Query logs for analytics
CREATE TABLE query_logs (
    id UUID PRIMARY KEY,
    query_text TEXT,
    detected_language VARCHAR(20),
    normalized_query TEXT,
    response TEXT,
    latency_ms INTEGER,
    created_at TIMESTAMP
);

-- Indexes
CREATE INDEX chunks_embedding_idx ON chunks USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX chunks_content_idx ON chunks USING GIN (to_tsvector('english', content));
```

### 3.4 Administration Layer *(Gap Addressed)*

- [ ] Document upload API endpoint
- [ ] Re-indexing trigger (manual + scheduled)
- [ ] Document versioning (track updates)
- [ ] Ingestion status dashboard

---

## Phase 4: Hybrid Retrieval Engine (Weeks 7-8)

### 4.1 Keyword Search (BM25-style)

- [ ] PostgreSQL full-text search with ranking
- [ ] Query tokenization + stemming
- [ ] Configurable weight for title/section matches

### 4.2 Semantic Search

- [ ] Query embedding generation (same model as chunks)
- [ ] Cosine similarity search with pgvector
- [ ] Top-K retrieval (configurable, default K=20)

### 4.3 Reciprocal Rank Fusion (RRF)

```python
def rrf_fusion(keyword_results, semantic_results, k=60):
    # RRF formula: score = 1/(k + rank)
    # Merge and re-rank both result sets
    # Return top-N fused results
```

- [ ] Implement RRF with configurable k parameter
- [ ] Experiment with different weights (0.5/0.5 baseline)
- [ ] Deduplication by chunk ID

### 4.4 Retrieval API

```python
POST /api/retrieve
{
    "query": "admission ke liye kya documents chahiye?",
    "top_k": 10,
    "use_hybrid": true
}
```

### 4.5 Comparative Testing *(Gap Addressed)*

- [ ] A/B testing framework: hybrid vs. keyword-only vs. semantic-only
- [ ] Log retrieval metrics for each query

---

## Phase 5: RAG & LLM Integration (Weeks 9-10)

### 5.1 LLM Provider Abstraction *(Gap Addressed)*

```python
class LLMProvider:
    primary = AnthropicClaude()
    fallback_1 = OpenAIGPT35()
    fallback_2 = OllamaLocal()  # Zero-cost offline
    
    async def generate(self, context, query):
        # Try primary, fallback on error/rate-limit
        # Circuit breaker pattern for repeated failures
```

### 5.2 Prompt Engineering

```
System: You are an admission policy assistant. 
Answer based ONLY on the provided context. 
Include citations [Document: Section, Page X].
Respond in the same language as the query.

Context: {retrieved_chunks}
Query: {user_query}
```

### 5.3 Citation System *(Gap Addressed)*

- [ ] Citation format: `[Doc Title: Section, Pg. X]`
- [ ] Multiple citations for multi-source answers
- [ ] Confidence indicator based on retrieval scores
- [ ] Frontend: Expandable citation cards showing excerpt

### 5.4 Response Generation

- [ ] Context assembly (top 5 chunks, max 4000 tokens)
- [ ] Streaming response support (SSE)
- [ ] Hallucination detection (check if answer references context)

### 5.5 Caching Layer *(Gap Addressed)*

- [ ] Query result cache (Redis, 24hr TTL)
- [ ] Embedding cache for repeated queries
- [ ] Cache hit/miss logging

---

## Phase 6: Backend API Development (Weeks 11-12)

### 6.1 API Endpoints

```
POST /api/chat              # Main chat endpoint
GET  /api/documents         # List indexed documents
POST /api/documents/upload  # Admin: upload new PDF
GET  /api/analytics/queries # Query statistics
GET  /api/health            # Health check
```

### 6.2 Security & Rate Limiting *(Gap Addressed)*

- [ ] slowapi integration with Redis backend
- [ ] Rate limits: 10 queries/minute, 100 queries/hour per IP
- [ ] API key authentication for admin endpoints
- [ ] CORS configuration for frontend domain
- [ ] Input validation & sanitization

### 6.3 Error Handling

- [ ] Structured error responses
- [ ] Graceful degradation (LLM down → return retrieved chunks)
- [ ] Retry logic with exponential backoff

### 6.4 Monitoring & Logging *(Gap Addressed)*

- [ ] Sentry integration for error tracking
- [ ] Custom logging middleware:
  - Query text, language, latency
  - Retrieval scores, LLM provider used
  - Cache hit/miss
- [ ] Daily analytics aggregation

---

## Phase 7: Frontend Development (Weeks 13-14)

### 7.1 Chat Interface

- [ ] Message input with auto-resize
- [ ] Chat history with scroll
- [ ] Loading states (typing indicator)
- [ ] Error messages with retry

### 7.2 Citation Display *(Gap Addressed)*

- [ ] Inline citation markers [1], [2]
- [ ] Hover tooltip with source preview
- [ ] Click to expand full citation card
- [ ] "View original document" link (if available)

### 7.3 Multilingual Support

- [ ] Language indicator (auto-detected)
- [ ] Right-to-left support (if Urdu script added later)
- [ ] Roman Urdu input examples/suggestions

### 7.4 Responsive Design

- [ ] Mobile-first layout
- [ ] Touch-friendly interactions
- [ ] Offline mode (show cached responses)

### 7.5 Admin Dashboard *(Optional)*

- [ ] Document management (upload, delete, re-index)
- [ ] Query analytics charts
- [ ] System health status

---

## Phase 8: Evaluation Framework (Weeks 15-17) ⭐ *Expanded*

### 8.1 Test Dataset Creation *(Gap Addressed)*

- [ ] **200 queries total:**
  - 80 English queries (formal + informal)
  - 80 Roman Urdu queries
  - 40 code-mixed queries
- [ ] **Collection method:**
  - 50 real student queries (survey current applicants)
  - 150 synthesized queries (based on common admission questions)
- [ ] **Ground truth annotations:**
  - Relevant document sections for each query
  - Expected answer key points

### 8.2 Retrieval Metrics

- [ ] Recall@5, Recall@10
- [ ] Precision@K
- [ ] Mean Reciprocal Rank (MRR)
- [ ] Comparison: Hybrid vs. Semantic-only vs. Keyword-only

### 8.3 Answer Quality Evaluation *(Gap Addressed)*

- [ ] **Human evaluation rubric:**

| Rating | Criteria |
|--------|----------|
| Correct | Accurate, complete, matches ground truth |
| Partially Correct | Accurate but incomplete |
| Incorrect | Factual error or hallucination |
| No Answer | System couldn't respond |

- [ ] **Evaluators:** 3-5 students + 1 admission office staff
- [ ] **Blind evaluation:** Evaluators don't know which configuration generated answer

### 8.4 Citation Accuracy

- [ ] Citation present when needed (Y/N)
- [ ] Citation correctly references source (Y/N)
- [ ] Citation includes page/section (Y/N)

### 8.5 Performance Metrics

- [ ] Average latency (target: <3s for response)
- [ ] P95 latency
- [ ] LLM API cost per 100 queries
- [ ] Cache hit rate

### 8.6 Error Analysis Pipeline *(Gap Addressed)*

- [ ] Automatic flagging of incorrect responses
- [ ] Categorization:
  - Retrieval failure (wrong chunks)
  - Normalization failure (Roman Urdu misunderstood)
  - LLM failure (hallucination, ignored context)
  - System error (timeout, API failure)
- [ ] Weekly error review meetings

---

## Phase 9: Deployment & Documentation (Weeks 18-20)

### 9.1 Production Deployment

- [ ] Backend: Railway.app (free tier, PostgreSQL included)
- [ ] Frontend: Vercel (free tier for academic projects)
- [ ] Database: Neon (already configured)
- [ ] Monitoring: Sentry (free tier)
- [ ] Domain: University subdomain or free domain

### 9.2 Load Testing *(Gap Addressed)*

- [ ] Locust script for concurrent user simulation
- [ ] Target: 50 concurrent users
- [ ] Identify bottlenecks (DB queries, LLM latency)
- [ ] Auto-scaling configuration

### 9.3 Documentation

- [ ] API documentation (auto-generated Swagger UI)
- [ ] User guide (for students)
- [ ] Admin guide (for admission office)
- [ ] Technical documentation (architecture, setup)
- [ ] Final thesis document
- [ ] Presentation slides

### 9.4 Buffer Time *(Gap Addressed)*

- [ ] 2 weeks buffer for unexpected delays
- [ ] Contingency: Simplify features if behind schedule

---

## Revised Timeline (20 Weeks + 2 Buffer)

| Phase | Weeks | Duration | Key Deliverables |
|-------|-------|----------|------------------|
| 1. Setup | 1-2 | 2 weeks | Repo, DB, CI/CD |
| 2. Roman Urdu | 3-4 | 2 weeks | Normalization module |
| 3. Documents | 5-6 | 2 weeks | Ingestion pipeline, KB |
| 4. Retrieval | 7-8 | 2 weeks | Hybrid engine with RRF |
| 5. RAG | 9-10 | 2 weeks | LLM integration, citations |
| 6. Backend | 11-12 | 2 weeks | Full API, security |
| 7. Frontend | 13-14 | 2 weeks | Chat UI, citation display |
| 8. Evaluation | 15-17 | 3 weeks | Dataset, metrics report |
| 9. Deployment | 18-20 | 3 weeks | Production system, docs |
| **Buffer** | 21-22 | 2 weeks | Catch-up, polish |

---

## Risk Mitigation (Updated)

| Risk | Impact | Mitigation |
|------|--------|------------|
| LLM API downtime | High | 3-tier fallback (Anthropic → OpenAI → Ollama) |
| Low Roman Urdu accuracy | High | Extended testing, manual rules fallback |
| Document format changes | Medium | Re-indexing pipeline, version tracking |
| High API costs | Medium | Caching, rate limits, local fallback |
| Insufficient test queries | Medium | Early data collection (start week 3) |
| Timeline delays | Medium | 2-week buffer, feature prioritization |

---

## Open Questions for User

1. **LLM Budget:** What's the monthly budget for LLM APIs? (~$50-100/month for Anthropic/OpenAI, or $0 for local Ollama)

2. **Roman Urdu Data:** Can you help collect Roman Urdu spelling variations from students, or should we use automated approaches only?

3. **Document Access:** Do you have the admission prospectus PDFs ready, or do we need to request them from the university?

4. **Evaluation Evaluators:** Who can perform human evaluation of answer quality? (fellow students, admission office staff?)

5. **Deployment Target:** Should this be deployed on university servers or public cloud (Vercel/Railway)?

6. **Authentication:** Should users need to log in, or should it be open access with rate limiting?

---

## Success Criteria

| Metric | Target |
|--------|--------|
| Retrieval Recall@5 | >80% |
| Answer Correctness (human eval) | >75% |
| Citation Accuracy | >90% |
| Average Response Time | <3 seconds |
| Roman Urdu Query Success | >70% |
| System Uptime | >95% |

---

## Appendix A: Key Research Questions (from Proposal)

1. Does hybrid retrieval improve retrieval accuracy compared to vector-only search?
2. Does query normalization enhance performance for Roman Urdu queries?
3. Can citation grounding reduce hallucinated responses?
4. How effective is the system in improving access to admission information?

---

## Appendix B: OBE Integration

| OBE Indicator | Contribution of Proposed System |
|---------------|--------------------------------|
| Enrollment Rate | Improves clarity of admission requirements |
| Admission Accuracy | Reduces incorrect applications |
| Student Retention | Helps students choose appropriate programs |
| Student Satisfaction | Provides instant access to admission information |
| Administrative Efficiency | Reduces repetitive inquiries to admission offices |

---

## Appendix C: Project Deliverables (from Proposal)

1. Web-based admission chatbot system
2. Structured admission knowledge base
3. Performance evaluation report
4. Source code repository
5. Deployment package
6. Final thesis document
7. Presentation and live demonstration

---

## Appendix D: Scope Boundaries

### Included
- Processing official undergraduate admission prospectus documents
- Answering admission-related queries (eligibility, documents, deadlines)
- Supporting queries in **English and Roman Urdu**
- Providing citation-based responses linked to official documents
- Web-based chatbot interface

### Excluded
- Predicting admission chances or merit rankings
- Processing admission applications
- Storing personal applicant data
- Replacing official admission authorities or decision-making systems

---

*Document Version: 1.0*

*Created: April 2, 2026*

*Next Review: End of Phase 1 (Week 2)*
