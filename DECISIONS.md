# Decision Log: Admission Policy Chatbot

> This document records every significant architectural, technical, and implementation decision made during this project. Each entry includes the decision, alternatives considered, rationale, and timestamp.

---

## Decision 001: Tech Stack Selection

**Date:** April 2, 2026 (from proposal)  
**Status:** ✅ Implemented  
**Deciders:** Project supervisor + implementation team

### Context
The project proposal specified a particular tech stack. We needed to decide whether to follow it exactly or make adjustments.

### Decision
Follow the proposal's tech stack with specific technology choices:
- Frontend: **Next.js 14** (not React alone, not Vue)
- Backend: **FastAPI** (not Flask, not Django)
- Database: **PostgreSQL with pgvector** (not MongoDB, not Pinecone)
- LLM: **Anthropic Claude** primary with fallbacks

### Alternatives Considered
| Alternative | Pros | Cons | Rejected Because |
|-------------|------|------|------------------|
| Flask | Simpler, more tutorials | No async support, slower | FastAPI has async + auto docs |
| Django | Full-featured, built-in admin | Heavy, overkill for API-only backend | Unnecessary complexity |
| MongoDB + Atlas Search | Easy vector search, no pgvector setup | Not relational, harder to maintain document-chunk relationship | Relational integrity needed |
| Pinecone/Weaviate | Purpose-built vector DBs | External service, vendor lock-in | PostgreSQL keeps everything self-contained |
| Vue.js | Good ecosystem | Less SSR support than Next.js | Next.js has better SSR + routing |

### Rationale
- FastAPI provides async support needed for LLM API calls and streaming
- Next.js SSR helps with SEO and initial page load
- PostgreSQL + pgvector keeps all data in one place (relational + vector)
- Anthropic Claude has better multilingual support and lower cost than GPT-4

---

## Decision 002: Embedding Model Selection

**Date:** April 2, 2026  
**Status:** ⚠️ Changed from original plan

### Context
Need sentence embeddings for semantic search. Original plan specified local multilingual model.

### Original Plan
`intfloat/multilingual-e5-large` — self-hosted, supports multiple languages including Roman Urdu

### Decision (Changed)
**Switched to OpenAI `text-embedding-3-small` API** for development

### Alternatives Considered
| Model | Size | Roman Urdu | Cost | Pros | Cons |
|-------|------|------------|------|------|------|
| multilingual-e5-large | 560MB | Good | Free (local) | No API needed, multilingual | Heavy download, needs GPU for speed |
| paraphrase-multilingual-mpnet-base-v2 | 420MB | Moderate | Free (local) | Smaller, faster | Less multilingual support |
| OpenAI text-embedding-3-small | API | Unknown (estimated good) | $0.02/1M tokens | No local compute, high quality | API cost, needs internet |
| OpenAI text-embedding-3-large | API | Unknown (estimated best) | $0.13/1M tokens | Best quality | More expensive |

### Rationale for Change
1. **Download timeout** — `sentence-transformers` + PyTorch download was too slow (500MB+ models)
2. **Resource constraints** — Dev machine has no GPU, local model inference would be very slow
3. **Development speed** — API embeddings are instant vs. minutes for local model download + inference
4. **1536 dimensions** — OpenAI model provides good embedding dimension for cosine similarity

### Trade-offs Accepted
- ✅ Faster development iterations
- ✅ No GPU dependency
- ❌ API cost per embedding (~$0.0001 per chunk)
- ❌ Needs internet connection
- ❌ May have lower Roman Urdu performance than multilingual-e5-large

### Migration Path
When PostgreSQL + production environment is available:
1. Switch `EMBEDDING_MODEL` config back to `intfloat/multilingual-e5-large`
2. Update `embeddings.py` to use `SentenceTransformer` instead of `OpenAI`
3. Re-index all documents (embeddings are model-specific)
4. Change embedding dimension from 1536 to 1024 in config and schema

---

## Decision 003: Database — SQLite Demo Mode Fallback

**Date:** April 2, 2026  
**Status:** ✅ Implemented as workaround  
**Priority:** 🔴 Critical

### Context
PostgreSQL was not available on the development machine. We needed a way to start the project without it.

### Decision
**Implement automatic SQLite fallback** when PostgreSQL is unavailable.

### Implementation
- `database.py` tries to connect to PostgreSQL
- If connection fails, automatically switches to `sqlite:///./admission_demo.db`
- Sets `USE_SQLITE = True` flag used by models to adjust schema

### Alternatives Considered
| Option | Pros | Cons |
|--------|------|------|
| Install PostgreSQL locally | Production-accurate testing | Requires sudo, system changes |
| Use Docker PostgreSQL container | Isolated, reproducible | Docker overhead, port conflicts |
| Use cloud PostgreSQL (Neon) | No local install needed | Needs internet, API account setup |
| SQLite fallback | Zero setup, instant start | No vector search optimization, different SQL dialect |

### Rationale
- **Immediate progress** — Could start building and testing without database setup blocker
- **Model compatibility** — SQLAlchemy models work with both SQLite and PostgreSQL
- **Easy migration** — Just change `DATABASE_URL` env var when PostgreSQL is available

### Known Issues
- No `pgvector` — embeddings stored as JSON strings (slower retrieval)
- No GIN index — full-text search not optimized
- No UUID type — using VARCHAR(36) instead
- Some SQL queries may differ (e.g., `datetime` vs `timestamp`)

---

## Decision 004: Roman Urdu Processing — Rule-Based vs. ML Model

**Date:** April 2, 2026  
**Status:** ✅ Implemented (rule-based)

### Context
Need to detect and normalize Roman Urdu queries. Original plan included `fasttext` ML model.

### Decision
**Implement rule-based language detection and normalization** instead of `fasttext` model.

### Detection Approach
- Pattern matching for common Roman Urdu question words (`kya`, `kaise`, `kahan`, `kab`, `kyun`)
- Verb form detection (`hai`, `tha`, `hoga`, `hain`)
- Possessive pronoun detection (`mera`, `teri`, `uska`, `hamara`)
- Common Roman Urdu admission vocabulary
- Score-based confidence calculation
- Falls back to `langdetect` library for baseline detection

### Normalization Approach
- Character mapping (aa→a, ee→e, oo→o) for double vowel normalization
- Word-level dictionary mapping for common misspellings
- Context-aware corrections using edit distance
- Support for both "normalize only" and "translate to English" modes

### Alternatives Considered
| Approach | Accuracy | Setup | Maintenance | Cost |
|----------|----------|-------|-------------|------|
| fasttext custom model | High | Complex (binary compilation) | Need training data | Free after setup |
| Custom classifier | Moderate | Medium | Need labeled data | Development time |
| Rule-based patterns | Moderate-High | Simple | Easy to add rules | Free |
| Google Translate API | High | Simple (API key) | Google maintains | API cost |

### Rationale
1. **fasttext compilation failed** — Binary wheels not available for Python 3.12
2. **No training data available** — Would need to collect and label hundreds of Roman Urdu queries
3. **Deterministic behavior** — Rules are transparent and debuggable
4. **Domain-specific** — Focused on admission vocabulary, not general Roman Urdu

### Known Limitations
- May misclassify heavily code-mixed queries
- Dictionary may not cover all spelling variations
- No learning from user corrections
- Rules are specific to admission domain, not general Roman Urdu

### Future Improvement
When training data is available:
1. Collect 500+ labeled Roman Urdu queries
2. Train `fasttext` or custom classifier
3. Compare accuracy against rule-based system
4. Replace if significant improvement

---

## Decision 005: LLM Provider Strategy — 3-Tier Fallback Chain

**Date:** April 2, 2026  
**Status:** ✅ Implemented

### Context
Need reliable LLM response generation with cost control and availability guarantees.

### Decision
**Implement 3-tier fallback chain** with circuit breaker pattern:
1. **Primary:** Anthropic Claude (`claude-3-haiku-20240307`)
2. **Fallback 1:** OpenAI GPT-3.5-turbo
3. **Fallback 2:** Ollama local model (`llama3:8b`)

### Circuit Breaker
- Each provider tracks failure count
- After 3 consecutive failures, provider is skipped
- Failures reset on success
- Prevents cascading failures

### Alternatives Considered
| Strategy | Reliability | Cost | Complexity |
|----------|-------------|------|------------|
| Single provider (Anthropic only) | Low (API downtime = total failure) | Medium | Simple |
| Single provider (OpenAI only) | Low (API downtime = total failure) | Medium | Simple |
| 2-tier fallback | Moderate | Medium-High | Moderate |
| 3-tier fallback | High | Variable | Higher |
| Load-balanced across providers | Highest | Highest | Complex |

### Rationale
- **Availability** — 3 providers means 2 must be down simultaneously for total failure
- **Cost control** — Falls back to zero-cost local model if APIs are down/unavailable
- **Circuit breaker** — Prevents wasting time on repeatedly failing providers
- **Claude first** — Better multilingual performance, lower cost than GPT-4

### Provider Selection Criteria
| Provider | Multilingual | Cost/1K tokens | Latency | Context Window |
|----------|--------------|----------------|---------|----------------|
| Claude 3 Haiku | Good | $0.25 input / $1.25 output | Fast (1-2s) | 200K |
| GPT-3.5-turbo | Good | $0.50 input / $1.50 output | Fast (1-2s) | 16K |
| Llama-3-8B (Ollama) | Unknown | Free (local) | Slow (5-10s, CPU) | 8K |

---

## Decision 006: Document Chunking Strategy

**Date:** April 2, 2026  
**Status:** ✅ Implemented

### Context
Need to split admission PDFs into chunks for embedding and retrieval.

### Decision
**Hybrid chunking strategy:**
1. **Section-based first** — Respect document structure (headers, sections)
2. **Fixed-size fallback** — 512 tokens with 50-token overlap for long sections
3. **Special handling for tables** — Keep tables intact when possible

### Chunk Size Parameters
| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Target chunk size | 512 tokens | Fits within LLM context, balances specificity vs. completeness |
| Overlap | 50 tokens | Ensures context continuity between adjacent chunks |
| Minimum chunk size | 100 tokens | Avoids trivial chunks |
| Max chunks from a section | Unlimited | Sections naturally limit chunk count |

### Alternatives Considered
| Strategy | Precision | Context | Implementation |
|----------|-----------|---------|----------------|
| Fixed-size only (512 tokens) | Low (breaks at arbitrary points) | Moderate overlap | Simplest |
| Section-based only | High | Full context | Fails for very long sections |
| Sentence-based | Very high | Low (fragments ideas) | Complex reassembly |
| **Hybrid (chosen)** | High | Good | Moderate complexity |

### Rationale
- **Admission documents have clear structure** — Sections like "Eligibility", "Fee Structure", "Deadlines"
- **Preserving section boundaries** improves retrieval accuracy (sections match query intent)
- **Overlap prevents context loss** at chunk boundaries
- **Tables treated specially** — Merit tables, fee schedules should stay together

---

## Decision 007: Reciprocal Rank Fusion (RRF) for Hybrid Search

**Date:** April 2, 2026  
**Status:** ✅ Implemented

### Context
Need to combine results from keyword search and semantic search.

### Decision
**Use Reciprocal Rank Fusion (RRF)** with configurable parameters:
- `k = 60` (RRF constant)
- `keyword_weight = 0.5`
- `semantic_weight = 0.5`

### RRF Formula
```
score(chunk) = Σ 1 / (k + rank_i)
```
Where `k` is a constant and `rank_i` is the rank of the chunk in result list `i`.

### Alternatives Considered
| Fusion Method | Effectiveness | Complexity | Tunability |
|---------------|---------------|------------|------------|
| Simple averaging of scores | Moderate | Simple | Low (score ranges differ) |
| Weighted sum of scores | Moderate | Simple | Medium (need to normalize scores) |
| **RRF (chosen)** | High | Simple | High (adjust k and weights) |
| Learning-to-rank (ML) | Highest | Complex | High (need training data) |
| Max score only | Low | Simplest | None |

### Rationale
1. **Score-agnostic** — RRF only uses rank, not raw scores (which differ between BM25 and cosine similarity)
2. **Proven effectiveness** — Research shows RRF outperforms simple fusion methods
3. **Simple to implement** — No training needed, just rank merging
4. **Configurable** — Can adjust weights for keyword vs. semantic emphasis
5. **k=60** — Literature suggests 60 is a good default that balances top-heavy vs. flat distributions

---

## Decision 008: Citation Format and System

**Date:** April 2, 2026  
**Status:** ✅ Implemented

### Context
Proposal requires citation-grounded responses. Need to define format and implementation.

### Decision
**Inline numeric citations** with expandable citation cards:

### Format
```
[1] Document Title: Section Name, p. 15-17
[2] Another Doc: Another Section, p. 3
```

### Implementation
- Citations generated from retrieved chunk metadata
- Each citation includes: document title, section header, page range, content preview
- Frontend displays citations as expandable cards
- Backend validates citations (checks for hallucinated references)

### Alternatives Considered
| Format | Readability | Actionability | Implementation |
|--------|-------------|---------------|----------------|
| Footnotes | High | Low (scroll to end) | Simple |
| Hyperlinks | Moderate | High (click to source) | Complex (need source viewer) |
| **Inline numeric (chosen)** | High | High (expandable cards) | Moderate |
| Full references in text | Low | High | Simple but clutters response |

### Rationale
- **Familiar format** — Matches academic paper citation style
- **Non-intrusive** — Doesn't break reading flow
- **Verifiable** — Users can check exact source location
- **Expandable** — Frontend can show/hide details on demand

---

## Decision 009: Prompt Engineering Strategy

**Date:** April 2, 2026  
**Status:** ✅ Implemented

### Context
Need to instruct LLM to respond based on retrieved context only, with citations, in the correct language.

### Decision
**Structured system prompt** with explicit rules:

```
You are an admission policy assistant for the University of Karachi.
Your role is to help prospective students understand admission requirements, procedures, and policies.

IMPORTANT RULES:
1. Answer ONLY based on the provided context. Do not use outside knowledge.
2. If the context doesn't contain enough information, say "I don't have enough information to answer this question."
3. Always include citations when making factual claims. Use the format [1], [2], etc.
4. Respond in the same language as the user's query (English or Roman Urdu).
5. Keep responses clear, concise, and easy to understand.
6. If asked about something not related to admissions, politely redirect to admission topics.
7. Do not predict admission chances or merit rankings.
8. Always remind users to verify information with official admission office.

Remember: Your responses must be grounded in the provided documents.
```

### Alternatives Considered
| Approach | Hallucination Risk | Cost | Flexibility |
|----------|-------------------|------|-------------|
| Simple prompt ("Answer the question") | High | Low | High |
| Structured rules (chosen) | Low | Low | Moderate |
| Few-shot examples | Lowest | Higher (more tokens) | Low (rigid) |
| XML-structured prompt | Low | Moderate | High |

### Rationale
- **Explicit rules reduce hallucination** — LLM knows exactly what's allowed
- **Language matching** — Critical for Roman Urdu support
- **Citation requirement** — Enforced by instruction, verified by code
- **Boundary rules** — Prevents answering non-admission questions or predicting merit

---

## Decision 010: Frontend Component Architecture

**Date:** April 2, 2026  
**Status:** ✅ Implemented

### Context
Need to build a chat interface with citations, multilingual support, and responsive design.

### Decision
**Component breakdown:**

| Component | Purpose | Type |
|-----------|---------|------|
| `page.tsx` | Main chat layout and state management | Client component |
| `ChatMessage.tsx` | Individual message bubbles (user/assistant) | Client component |
| `ChatInput.tsx` | Textarea with auto-resize and submit | Client component |
| `CitationCard.tsx` | Expandable citation source card | Client component |
| `TypingIndicator.tsx` | Animated "typing" dots | Client component |

### State Management
- **Local state** — `useState` in `page.tsx` for messages array
- **No external state library** — Too simple for Redux/Zustand
- **API calls** — `fetch` directly, no React Query/SWR (yet)

### Alternatives Considered
| Architecture | Complexity | Performance | Scalability |
|--------------|------------|-------------|-------------|
| All-in-one component | Low | Moderate | Poor |
| **Component split (chosen)** | Moderate | Good | Good |
| Redux + component tree | High | Best | Best (overkill) |
| Server components | Moderate | Best | Good (limited client interactivity) |

### Rationale
- **Single source of truth** — `page.tsx` manages all message state
- **Reusable components** — `ChatMessage` used for both user and assistant messages
- **Auto-resize textarea** — Better UX than fixed input field
- **Expandable citations** — Don't clutter UI with all details upfront

---

## Decision 011: CI/CD Pipeline Structure

**Date:** April 2, 2026  
**Status:** ✅ Implemented

### Decision
**Separate CI pipelines** for backend and frontend:

### Backend Pipeline (`.github/workflows/backend-ci.yml`)
1. **Lint** — Ruff check
2. **Test** — Pytest (with PostgreSQL service container)
3. **Build** — Import verification

### Frontend Pipeline (`.github/workflows/frontend-ci.yml`)
1. **Lint** — ESLint
2. **Build** — `npm run build`

### Alternatives Considered
| Approach | Speed | Isolation | Maintenance |
|----------|-------|-----------|-------------|
| **Separate pipelines (chosen)** | Fast (parallel) | High | Moderate (2 files) |
| Single combined pipeline | Slow (sequential) | Low | Simple (1 file) |
| Monorepo tools (Turborepo, Nx) | Fast | High | Complex setup |

### Rationale
- **Parallel execution** — Backend and frontend can test simultaneously
- **Path filtering** — Only run backend CI when `backend/**` changes
- **PostgreSQL service** — Backend tests run against real PostgreSQL in CI
- **Build verification** — Ensures `npm run build` passes before merge

---

## Decision 012: Evaluation Dataset Format

**Date:** April 2, 2026  
**Status:** ⚠️ Partial (30/200 queries)

### Decision
**CSV format** with columns: `query`, `expected_language`, `expected_topics`, `notes`

### Query Distribution
| Language | Count | Percentage |
|----------|-------|------------|
| English | 80 | 40% |
| Roman Urdu | 80 | 40% |
| Code-mixed | 40 | 20% |

### Alternatives Considered
| Format | Readability | Tool Support | Version Control |
|--------|-------------|--------------|-----------------|
| **CSV (chosen)** | High | Universal (Excel, Python, R) | Good |
| JSON | Moderate | Good | Moderate (nested structure) |
| YAML | High | Moderate | Good |
| SQL | Low | Database only | Poor |

### Rationale
- **Simple to edit** — Can be opened in any spreadsheet tool
- **Easy to parse** — `csv` module in Python handles it natively
- **Version control friendly** — Plain text, diffs are readable
- **Extensible** — Can add columns without breaking existing tools

---

## Decision 013: Docker Compose Configuration

**Date:** April 2, 2026  
**Status:** ✅ Implemented

### Decision
**4-service compose:**
1. `postgres` — PostgreSQL with pgvector
2. `redis` — Redis for caching and rate limiting
3. `backend` — FastAPI application
4. `frontend` — Next.js application

### Alternatives Considered
| Approach | Complexity | Reproducibility | Resource Usage |
|----------|------------|-----------------|----------------|
| **Docker Compose (chosen)** | Moderate | High | Moderate |
| Manual install | High | Low | Low |
| Kubernetes | Very high | Very high | High |
| Single Dockerfile | Low | Moderate | Low (everything in one container) |

### Rationale
- **Development parity** — Same setup as production
- **One-command setup** — `docker-compose up` starts everything
- **Service isolation** — Each component in its own container
- **Health checks** — Services wait for dependencies to be ready

---

## Decision 014: Project Documentation Structure

**Date:** April 2, 2026  
**Status:** ✅ Created

### Decision
**Three documentation files:**
1. `README.md` — Quick start and overview
2. `CONTEXT.md` — Comprehensive project state (for AI continuation)
3. `DECISIONS.md` — Decision log (this file)
4. `docs/IMPLEMENTATION_PLAN.md` — 20-week phased plan

### Alternatives Considered
| Approach | Completeness | AI-Friendly | Maintenance |
|----------|--------------|-------------|-------------|
| **Multi-file (chosen)** | High | High | Moderate |
| Single README | Low | Low | Simple |
| Wiki (GitHub) | Moderate | Moderate | External tool |
| No documentation | None | None | None |

### Rationale
- **README for humans** — Quick start, not exhaustive
- **CONTEXT.md for AI** — Structured, machine-parseable project state
- **DECISIONS.md for future** — "Why did we do it this way?" answered
- **IMPLEMENTATION_PLAN.md for tracking** — Phased milestones

---

## Decision 015: Branch Naming and Push Strategy

**Date:** April 2, 2026  
**Status:** ✅ Implemented

### Decision
- **Branch name:** `initial-prototype`
- **First commit message:** Conventional commit with comprehensive description
- **Push strategy:** Push complete prototype before merging to `main`

### Alternatives Considered
| Strategy | Safety | Review | Speed |
|----------|--------|--------|-------|
| **Feature branch + push (chosen)** | High (isolated from main) | Easy (PR review) | Fast |
| Direct to main | Low | Harder to rollback | Fastest |
| Small incremental commits | High | Easy review per commit | Slow |

### Rationale
- **Isolated from main** — Can experiment without breaking anything
- **Reviewable** — Pull request shows all changes at once
- **Descriptive commit** — Single commit captures the full initial build

---

## Decision 016: Excluded Features (Scope Boundaries)

**Date:** April 2, 2026 (from proposal)  
**Status:** Enforced in implementation

### Explicitly Excluded
The following are NOT part of this project:

| Excluded Feature | Reason |
|-----------------|--------|
| Admission chance prediction | Requires historical data, ML model, could be misleading |
| Application processing | Not a workflow system, only informational |
| Personal applicant data storage | Privacy concerns, GDPR compliance complexity |
| Replacement for admission authorities | System is advisory, not authoritative |
| Urdu script support | Scope limited to Roman Urdu (future work) |
| Mobile application | Web-based only (future work) |
| Voice-based interface | Text-only (future work) |
| Postgraduate admissions | Undergraduate only (future expansion) |

### Rationale
These exclusions are from the original proposal to keep the project scope manageable and legally compliant.

---

## Decision 017: OBE Integration Approach

**Date:** April 2, 2026 (from proposal)  
**Status:** Documented, not implemented

### Decision
**Position the system as an "Admission Information Support Module"** within the OBE framework.

### OBE Indicators Addressed
| Indicator | How Chatbot Contributes |
|-----------|------------------------|
| Enrollment Rate | Improves clarity of admission requirements → more complete applications |
| Admission Accuracy | Reduces incorrect applications through accurate information |
| Student Retention | Helps students choose appropriate programs → better fit |
| Student Satisfaction | Provides instant access to admission information |
| Administrative Efficiency | Reduces repetitive inquiries to admission offices |

### Rationale
- OBE integration is **indirect** — the chatbot operates in the pre-enrollment phase
- **Measurable impact** — Can track reduction in admission office inquiries
- **Documented contribution** — Clear mapping to institutional performance indicators

---

## Summary of Changed Decisions

| # | Decision | Original Plan | Actual Implementation | Reason for Change |
|---|----------|---------------|----------------------|-------------------|
| 002 | Embedding Model | Local multilingual-e5-large | OpenAI text-embedding-3-small API | Download timeout, no GPU |
| 003 | Database | PostgreSQL only | SQLite fallback | PostgreSQL not installed |
| 004 | Roman Urdu Processing | fasttext ML model | Rule-based patterns | fasttext compilation failed |

---

## Open Questions (Unresolved Decisions)

### Q1: Production LLM Budget
- **Question:** What's the monthly budget for LLM API calls?
- **Impact:** Determines which providers can be used as primary
- **Options:** $0 (Ollama only), $50 (OpenAI GPT-3.5), $100+ (Claude/GPT-4)
- **Status:** ⏳ Pending user input

### Q2: Document Collection
- **Question:** Do we have admission prospectus PDFs ready?
- **Impact:** Cannot test retrieval without documents
- **Status:** ⏳ Need to obtain from University of Karachi

### Q3: Evaluation Evaluators
- **Question:** Who will perform human evaluation of answer quality?
- **Impact:** Quality of evaluation results
- **Options:** Fellow students, admission office staff, supervisor
- **Status:** ⏳ Pending user input

### Q4: Deployment Target
- **Question:** University servers or public cloud (Vercel/Railway)?
- **Impact:** Infrastructure setup, cost, accessibility
- **Status:** ⏳ Pending user input

### Q5: Authentication
- **Question:** Should the system require user login?
- **Impact:** Rate limiting strategy, user tracking, privacy
- **Options:** Open access with rate limiting, optional login, required login
- **Status:** ⏳ Pending user input

---

## Appendix: Technology Versions at Time of Decisions

| Technology | Version | Date Verified |
|------------|---------|---------------|
| Python | 3.12.3 | April 2, 2026 |
| Node.js | 24.13.0 | April 2, 2026 |
| npm | 11.6.2 | April 2, 2026 |
| FastAPI | 0.135.3 | April 2, 2026 |
| Next.js | 14.1.0 | April 2, 2026 |
| TailwindCSS | 3.4.1 | April 2, 2026 |
| SQLAlchemy | 2.0.48 | April 2, 2026 |
| PyMuPDF | 1.27.2.2 | April 2, 2026 |
| OpenAI Python SDK | 2.30.0 | April 2, 2026 |
| Anthropic Python SDK | 0.88.0 | April 2, 2026 |
