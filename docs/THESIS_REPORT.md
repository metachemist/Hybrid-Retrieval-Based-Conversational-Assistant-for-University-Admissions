# Design and Implementation of a Hybrid Retrieval-Based Conversational Assistant for University Admission Policies

**A Final Year Project Thesis**

Submitted in partial fulfillment of the requirements for the degree of Bachelor of Science

**Supervisor:** Miss Humaira Tariq
**Institution:** University of Karachi

---

## Abstract

University admission policies are typically distributed across lengthy, technically written prospectus documents, fee schedules, and closing-merit notices that are difficult for prospective students to interpret. As a result, many applicants rely on informal sources — social media groups, seniors, or word of mouth — which frequently produce misinformation and incorrect applications. This thesis presents the design, implementation, and evaluation of a hybrid retrieval-based conversational assistant that answers admission-related questions for the University of Karachi using Retrieval-Augmented Generation (RAG).

The system combines PostgreSQL full-text search with pgvector-based semantic similarity search, merged through Reciprocal Rank Fusion (RRF), to retrieve relevant passages from official admission documents. Retrieved passages are passed to a Large Language Model (LLM) that generates a citation-grounded answer, with automatic failover across four LLM providers (OpenAI, Gemini, Anthropic, and a local Ollama model) to maintain availability under free-tier rate limits. A dictionary-based Roman Urdu language detector and normalizer allow the system to accept informal, code-mixed queries such as *"admission ke liye kya documents chahiye?"* alongside standard English. The system is exposed through a Next.js chat interface with authentication, and an administrative dashboard that visualizes query volume, language distribution, topic breakdown, and response performance drawn from logged interactions.

The system was evaluated on a 41-query benchmark spanning English, Roman Urdu, and mixed-language queries, using retrieval recall/MRR against a manually labeled ground truth and an LLM-as-judge groundedness score. Hybrid retrieval matched or exceeded keyword-only and semantic-only retrieval on Recall@5 (76.3%) and Recall@10 (84.2%), while citation-marker validity reached 100%. Generation quality — 68.3% of responses judged grounded or partially grounded, with an average latency of 3.8 seconds — fell short of the proposal's original targets, and the results chapter discusses these gaps candidly, including a 31.7% no-answer rate and the small size of the evaluation set. The project demonstrates a working, end-to-end, citation-grounded, multilingual admission assistant while identifying specific, evidence-based directions — larger evaluation sets, human-verified judging, and caching/rate-limiting completion — for future improvement.

---

## Table of Contents

1. Introduction
2. Literature Review
3. Problem Statement, Objectives, and Research Questions
4. System Design and Architecture
5. Implementation
6. Evaluation and Results
7. Conclusion, Limitations, and Future Work

References
Appendix A: Evaluation Dataset Sample
Appendix B: API Reference

---

## Chapter 1: Introduction

### 1.1 Background

University admission procedures involve complex, interlocking policies: eligibility criteria that vary by faculty and programme, document checklists, fee schedules that differ between self-finance and open-merit seats, and closing-merit lists that change every admission cycle. At large public-sector universities such as the University of Karachi, this information is published across dozens of separate PDF prospectuses, scanned notices, and image-based advertisements (see `FYP DOCUMENTS/` in the project repository — 29 distinct source documents spanning morning/evening programmes, self-finance schedules, scholarship notices, and closing-merit lists for multiple years). A prospective student trying to answer a simple question — "what documents do I need for BS Computer Science evening programme?" — must locate, cross-reference, and correctly interpret several of these documents simultaneously.

This friction has two consequences. First, students turn to informal channels (WhatsApp groups, forums, senior students) that are fast but unreliable, leading to missed deadlines and rejected applications. Second, admission offices absorb a large volume of repetitive queries that could, in principle, be answered directly from documents the office has already published.

### 1.2 Motivation

Retrieval-Augmented Generation (RAG) offers a way to close this gap without asking a university to build or maintain a hand-crafted FAQ system. Instead of relying on a language model's parametric knowledge (which for a specific university's 2026 admission cycle would not exist in any pretrained model, and which is prone to hallucination when it does not), a RAG system retrieves the actual relevant passages from official documents at query time and constrains the language model to answer from that retrieved context, with citations back to the source. This directly addresses the two failure modes above: answers are grounded in the university's own published policy, and the citation trail lets a student verify a claim against the original document rather than trusting the chatbot outright.

A second, Pakistan-specific motivation is language. Many prospective students phrase admission questions informally, in Roman Urdu or a mix of Roman Urdu and English (e.g., *"kal last date hai kya admission ke liye?"*). Most existing university chatbots and FAQ systems are English-only, or treat Roman Urdu queries as noise. Supporting this register of language is a secondary but deliberate goal of the project.

### 1.3 Project Summary

This thesis documents the design and implementation of an admission-policy conversational assistant built around four cooperating layers: a document ingestion pipeline that parses and chunks official PDFs; a hybrid retrieval engine that fuses keyword and semantic search; an answer-generation layer that prompts an LLM to produce citation-grounded responses with automatic provider failover; and a web interface (chat + authentication + an admin analytics dashboard) built with Next.js and FastAPI. The system was evaluated against a hand-labeled query set covering English, Roman Urdu, and mixed-language queries, and the results — including where the system falls short of its original targets — are reported and discussed in Chapter 6.

---

## Chapter 2: Literature Review

### 2.1 Chatbots in Educational Support Systems

Conversational agents have been applied across academic advising, administrative FAQ handling, and learning support in higher education. Their appeal in an administrative context is straightforward: admission and enrollment queries are high-volume, repetitive, and largely answerable from a fixed corpus of institutional documents, which makes them well suited to automation compared to open-ended tutoring or advising tasks. However, systems built as rule-based FAQ bots or intent classifiers tend to be brittle — they require the query to closely match a pre-anticipated phrasing, and they degrade badly on paraphrased or informally worded questions, which is precisely how prospective students write.

### 2.2 Retrieval-Augmented Generation

RAG addresses the brittleness of both pure rule-based systems and pure parametric LLM answering by separating *retrieval* (finding relevant source material) from *generation* (composing a natural-language answer from that material). Because the model is instructed to answer only from retrieved context, RAG substantially reduces hallucination relative to closed-book generation, and — critically for an administrative use case — it allows the knowledge base to be updated simply by re-ingesting new documents, without retraining or fine-tuning any model. This project follows the now-standard RAG pattern: chunk documents → embed and index chunks → retrieve top-k chunks per query → construct a prompt that includes the chunks as context → generate a cited answer.

### 2.3 Hybrid Information Retrieval

Pure dense (embedding-based) retrieval is known to underperform on queries containing exact terms that matter precisely because they are exact — programme names, document titles, specific numeric fee figures, or codes — because embedding models compress such tokens into a continuous space that can blur precise lexical distinctions. Pure keyword retrieval (e.g., BM25 or PostgreSQL full-text search) preserves exact-term matching but misses paraphrases and synonyms. Hybrid retrieval, most commonly implemented by running both search strategies independently and merging their ranked lists with **Reciprocal Rank Fusion (RRF)**, is reported in the literature to outperform either method alone on domains involving technical or policy-heavy documents, since it captures both lexical precision and semantic recall. This project adopts RRF as its fusion strategy (Chapter 4/5), and Chapter 6 empirically re-examines this claim against this project's own admission-document corpus and query set — with a more mixed result than the literature would predict, which is discussed there.

### 2.4 Multilingual and Roman Urdu NLP

Roman Urdu — Urdu written in Latin script, common in SMS, WhatsApp, and informal web text across Pakistan — lacks a standardized orthography. The same word may be spelled several different ways (e.g., *chahiye*, *chaiye*, *chiye*), and it is frequently code-mixed with English within a single sentence. This is a known, hard problem in South Asian NLP: because there is no single canonical spelling to normalize toward, dictionary/rule-based approaches (as used in this project) must enumerate observed variants by hand rather than deriving them systematically, and statistical/ML transliteration approaches require labeled Roman Urdu corpora that are scarce, especially in a narrow domain like university admissions.

### 2.5 Research Gap

Reviewing systems in the admission-chatbot space, existing tools rarely combine three properties simultaneously: (1) citation-grounded answers traceable to an official source document, (2) hybrid retrieval rather than a single search strategy, and (3) support for informal, code-mixed Roman Urdu queries. Most published or deployed university chatbots handle only formally phrased English queries and do not expose their evidence trail to the user. This project targets that combination directly, in the specific institutional context of University of Karachi undergraduate admissions.

---

## Chapter 3: Problem Statement, Objectives, and Research Questions

### 3.1 Problem Statement

Prospective students at the University of Karachi face difficulty understanding admission policies due to complex, dispersed documentation and the absence of interactive guidance. No existing system at the university interprets official admission documents and answers informally phrased student queries — in English or Roman Urdu — with verifiable, citation-backed accuracy.

### 3.2 Objectives

**Primary objective.** To design and implement a hybrid retrieval-based conversational assistant that provides accurate, citation-grounded responses to admission-related queries.

**Secondary objectives:**

1. Construct a structured knowledge base from official admission documents.
2. Develop a query-normalization module for informal English and Roman Urdu.
3. Implement hybrid retrieval using keyword and semantic search, fused with RRF.
4. Integrate a RAG-based answer-generation pipeline with citation grounding.
5. Evaluate system performance using a labeled set of realistic student queries.
6. Develop a usable, authenticated web interface with administrative analytics.

### 3.3 Research Questions

1. Does hybrid retrieval improve retrieval accuracy compared to vector-only (semantic) search?
2. Does query normalization enhance performance for Roman Urdu queries?
3. Can citation grounding reduce hallucinated responses?
4. How effective is the system in improving access to admission information?

Chapter 6 answers each of these questions directly, against the evaluation data collected in this project — including a nuanced answer to Question 1, where the data only partially supports the hypothesis motivating hybrid retrieval in the first place.

### 3.4 Scope

**Included:** processing official undergraduate admission prospectus documents; answering queries on eligibility, required documents, fees, deadlines, and merit-related procedure; supporting English and Roman Urdu queries; citation-based responses linked to source documents; a web-based chat interface with optional authentication and an admin dashboard.

**Excluded:** predicting individual admission chances or merit-list outcomes; processing or submitting admission applications; storing sensitive personal applicant data; replacing the university's official admission office as a decision-making authority.

---

## Chapter 4: System Design and Architecture

### 4.1 Architectural Overview

The system follows a five-layer architecture:

```
 ┌─────────────────────────────────────────────────────────┐
 │  Client Layer — Next.js 14 (TypeScript, Tailwind)        │
 │  Chat UI · Auth pages · Admin analytics dashboard         │
 └───────────────────────────┬─────────────────────────────┘
                              │ REST / SSE (fetch)
 ┌───────────────────────────▼─────────────────────────────┐
 │  API Layer — FastAPI (Python 3.11+)                      │
 │  /api/chat · /api/documents · /api/auth · /api/admin ·    │
 │  /api/health   (JWT auth, optional on /chat, required on  │
 │  /admin/* and document-write routes)                      │
 └───────────────────────────┬─────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
 ┌─────────────┐     ┌──────────────────┐   ┌────────────────┐
 │ Retrieval    │     │ Generation Layer  │   │ Roman Urdu      │
 │ Layer        │     │ (RAG prompt +     │   │ Layer           │
 │ keyword +    │     │  LLM provider     │   │ LanguageDetector│
 │ semantic +   │     │  chain: OpenAI →  │   │ + Normalizer    │
 │ RRF fusion   │     │  Gemini → Claude  │   └────────────────┘
 └──────┬───────┘     │  → Ollama)         │
        │             └──────────────────┘
        ▼
 ┌─────────────────────────────────────────┐
 │  Data Layer — Neon PostgreSQL + pgvector  │
 │  documents · chunks (768-dim embedding) · │
 │  users · query_logs                       │
 └─────────────────────────────────────────┘
        ▲
        │ offline
 ┌──────┴──────────────────────────────────┐
 │ Administration / Ingestion Layer          │
 │ PyMuPDF parse → clean → section-split →   │
 │ chunk (table-aware) → embed → index       │
 └───────────────────────────────────────────┘
```

A user query enters through the Client Layer, is normalized by the Roman Urdu layer if informal/mixed-language, retrieved against the Data Layer by the Retrieval Layer, and answered by the Generation Layer using only the retrieved passages as context. Every query and its outcome (latency, provider used, detected language, classified topic) is logged to `query_logs`, which is the sole data source for the Administration Layer's analytics dashboard — the dashboard performs no separate data collection of its own.

### 4.2 Data Model

Four tables implement the schema (Neon PostgreSQL, `pgvector` extension enabled):

| Table | Key columns | Purpose |
|---|---|---|
| `documents` | `id` (UUID), `title`, `year`, `source_path`, `ingested_at` | One row per ingested prospectus/notice PDF |
| `chunks` | `id`, `doc_id` (FK), `content`, `embedding` (`vector(768)`), `section_header`, `page_start`, `page_end`, `chunk_type`, `chunk_order` | Retrieval unit; 1:N with `documents`, cascade-deleted with parent |
| `users` | `id`, `email` (unique), `password_hash`, `role` (`user`/`admin`), `reset_token`, `reset_token_expires` | Authentication; supports password-reset flow |
| `query_logs` | `id`, `query_text`, `detected_language`, `normalized_query`, `response`, `latency_ms`, `llm_provider`, `topic`, `user_id` (FK, nullable), `created_at` | Every chat request/response, whether authenticated or anonymous; sole source for admin analytics |

The embedding column is fixed at 768 dimensions to match the Matryoshka-truncated output of the primary embedding model (Section 5.2); this is a schema-level design constraint that any alternative embedding model must be truncated or padded to match.

### 4.3 Retrieval Design

Two independent search strategies run per query and are fused rather than one being chosen over the other:

- **Keyword search** uses PostgreSQL's native full-text search (`to_tsquery`), ranked by `ts_rank`. Query terms are joined with logical OR rather than AND, a deliberate design decision (see Section 5.1) to avoid returning zero results for natural multi-word questions.
- **Semantic search** uses pgvector cosine distance between the query embedding and each chunk's stored embedding.
- **Fusion** merges the two ranked lists with Reciprocal Rank Fusion, `score = Σ weight / (k + rank + 1)`, with `k = 60` (the standard RRF constant from the literature) and equal 0.5/0.5 weighting between keyword and semantic scores. Each sub-search retrieves a candidate pool of `2 × top_k` before fusion, so the final top-k is chosen from a wider pool than either method alone would surface.

This design directly operationalizes the hybrid-retrieval hypothesis from Chapter 2 and Research Question 1; Chapter 6 reports how well it actually performs relative to either method run alone.

### 4.4 Generation Design

The generation layer is intentionally decoupled from any single LLM vendor. A provider-abstraction interface (`LLMProviderBase`) is implemented four times (OpenAI, Gemini, Anthropic, Ollama) and composed into an ordered fallback chain with a per-provider circuit breaker (three consecutive failures trips the breaker and skips that provider for subsequent requests until it succeeds again). This design choice is driven by a practical constraint specific to this project: free-tier LLM APIs (Gemini in particular) impose strict per-minute/per-day quotas that a single evaluation run or a burst of concurrent users can exhaust, so the system needs to degrade to an alternative provider rather than fail outright.

### 4.5 Multilingual Design

Rather than translating Roman Urdu queries into English before retrieval (which would require a translation step of its own, with its own error surface), the default configuration normalizes *spelling* only — collapsing spelling variants of the same Roman Urdu word to a canonical form — while leaving the language itself as Roman Urdu. This keeps the query in the same register the underlying multilingual embedding model was designed to handle, and lets the LLM mirror the user's language in its response, per the system prompt's explicit instruction to do so.

---

## Chapter 5: Implementation

### 5.1 Document Ingestion Pipeline

Ingestion is implemented in `scripts/ingest_documents.py` and is runnable both as a standalone CLI (`python scripts/ingest_documents.py <path>`) and inline from the admin document-upload API route, so the same code path handles bulk offline ingestion and ad-hoc uploads through the UI.

PDF text is extracted per-page with PyMuPDF (`fitz`), then cleaned with a noise-pattern filter that strips page numbers, repeated "University of Karachi" running headers, and boilerplate lines that would otherwise pollute every chunk's embedding. A section-splitting pass (`extract_with_sections`) scans the first five lines of each page for header-like patterns (chapter markers, numbered headings, all-caps lines, domain keywords like "ELIGIBILITY" or "FEE") and tags subsequent content with that section header; any content preceding the first detected header is retained under a generic `"General"` section rather than being dropped, so the extraction is lossless even when header detection misses.

Chunking (`DocumentChunker`) targets ~512 tokens per chunk with a 50-token overlap between consecutive chunks, and treats tabular content specially: three or more consecutive delimited rows are detected and split **one row per chunk**, with the header row prepended to each. This was a deliberate response to how admission documents actually present information — fee schedules and closing-merit tables list dozens of departments' figures in one table, and embedding the whole table as a single chunk would dilute the vector representation of, e.g., "BS Computer Science fee" among thirty unrelated rows in the same embedding. Non-tabular prose is chunked by paragraph, falling back to sentence-level and then word-boundary splitting for oversized paragraphs.

Each chunk is embedded individually (not batched) and written to the `chunks` table along with its section header, page range, and chunk type, giving every retrieved passage a traceable page-level citation.

### 5.2 Embedding Model

The embedding model selection evolved over the project (see commit history: `33a1f9d`, `619aa54`, `98d8372`). The current implementation uses Google's `gemini-embedding-001` via the `google-genai` SDK as the primary embedding model, with its output truncated from a native 3072 dimensions to 768 dimensions using Matryoshka representation learning (the `output_dimensionality` parameter). OpenAI's `text-embedding-3-small` serves as a fallback when Gemini's free-tier quota is exhausted (HTTP 429) or unreachable, and is explicitly called with `dimensions=768` in that case to remain compatible with the fixed 768-dimension `chunks.embedding` column. This is a pragmatic cost/availability decision rather than a claim that Gemini's embedding is qualitatively superior: both models are OpenAI/Google general-purpose text embedding models rather than domain-specialized or Urdu-specialized models, which is a limitation discussed in Chapter 7.

### 5.3 Hybrid Retrieval Engine

`HybridRetriever` (`backend/app/services/retrieval/hybrid_retriever.py`) implements the design described in Section 4.3. Two implementation details are worth surfacing precisely, since they shaped the results in Chapter 6:

- Keyword search uses `to_tsquery('english', term1 | term2 | ...)` — an OR of individual terms — rather than `plainto_tsquery`, which would AND every term together and, per the module's own documentation, returned zero results for natural multi-word questions during development. This makes the "keyword" baseline in Chapter 6 considerably more recall-friendly than a naive AND-based keyword search would be, which is relevant context for interpreting why it performs competitively with the hybrid configuration.
- RRF fusion uses `k = 60` and equal weighting; both are configurable via `Settings` (`RRF_K`, `RRF_WEIGHT_KEYWORD`, `RRF_WEIGHT_SEMANTIC`) but were not tuned against the evaluation set in this project — they use the standard literature defaults, which Chapter 7 flags as an unexplored optimization opportunity.

### 5.4 Roman Urdu Processing

Both the language detector and the normalizer (`backend/app/services/roman_urdu/`) are rule-based rather than statistical, reflecting the scarcity of labeled Roman Urdu training data noted in Chapter 2.

`LanguageDetector` combines the general-purpose `langdetect` library with a hand-built scoring heuristic specific to this domain: regex patterns for Roman Urdu question words and verb forms, a curated ~30-word list of admission-domain Roman Urdu terms and their common misspellings (e.g., *kal*, *kull*, *chahiye*, *chaiye*), and elongated-vowel detection (repeated vowels such as *aa*, *ee* are a common Roman Urdu orthographic feature). A combined score above 0.5 classifies the query as Urdu or mixed depending on what the base `langdetect` call reported.

`RomanUrduNormalizer` maps spelling variants to a canonical form using a curated ~50-entry dictionary, deliberately excluding short tokens that are ambiguous between Roman Urdu and English (*or*, *to*, *main*, *par*, *he*) to avoid corrupting genuinely English or code-mixed input. Vowel-elongation collapsing (`aa→a`, `ee→e`) is applied only to words already recognized via the word-mapping dictionary, not blindly to all input — an explicit guard against corrupting English words such as "class" or "application" that happen to contain double vowels. The production request path (`chat.py`) runs the normalizer in spelling-normalization mode rather than translation mode, so a Roman Urdu query stays in Roman Urdu (spelling-standardized) through retrieval and generation, rather than being machine-translated to English.

### 5.5 Answer Generation

`create_rag_prompt` (`backend/app/services/rag/prompt.py`) assembles retrieved chunks into a numbered context block (`[1] {chunk text}` with a `Source / Section / Pages` line beneath each), in the order chunks arrive from the fused retrieval ranking, up to a maximum of 10 chunks per request. The system prompt instructs the model, in nine explicit rules, to answer only from the supplied context, decline with a fixed phrase when the context is insufficient, cite claims with `[N]` markers, mirror the user's input language, never predict individual merit outcomes, always recommend verifying with the admission office, and — a detail specific to this domain — reproduce numeric figures verbatim, including South Asian lakh-style comma grouping (e.g., "6,50,000"), rather than reformatting them.

LLM generation is routed through a four-provider fallback chain — OpenAI (primary) → Gemini → Anthropic Claude → a local Ollama model (last resort, zero-cost) — with a per-provider circuit breaker that skips a provider after three consecutive failures. This ordering, verified directly against the current implementation (`llm_provider.py`), differs from the provider priority described in the project's README and initial planning documents (which describe Gemini as primary); the code evolved toward an OpenAI-primary configuration for reliability during evaluation, and this discrepancy is noted here rather than silently reconciled, since it reflects a real implementation decision made after the proposal was written.

### 5.6 Web Application

The frontend is a Next.js 14 App Router application. The primary chat page renders user and assistant messages differently, rendering assistant responses through `react-markdown`, and attaches a metadata row to each assistant reply — response latency, the LLM provider that answered, and a detected-language badge (English / Roman Urdu / Mixed) — together with a collapsible list of citation cards, each showing the source document title, section, and page range, with an expandable content preview. Authentication (JWT, `python-jose` + `passlib` bcrypt hashing) is optional on the chat endpoint — anonymous users can converse with the assistant, but authenticated users have their queries attributed in `query_logs` — and required for the admin document-management and analytics routes.

The admin dashboard (`admin/page.tsx`), specified in `PLAN.md` against a reference dashboard layout, presents four KPI cards (total queries, average response time, cache-hit rate, success rate) alongside a query-volume area chart and language/topic breakdown bar charts, all computed live from `query_logs` over a selectable 7/30/90-day window via six dedicated `/api/admin/analytics/*` endpoints.

### 5.7 Known Implementation Gaps

Two features present in configuration but not wired into the request path are worth stating plainly, since they affect how the evaluation results in Chapter 6 should be read:

- **Caching** — `CACHE_TTL_SECONDS` and a Redis connection are configured, and `cache_hit` is a real column in `query_logs`, but no cache lookup is actually performed in `chat.py`; every request currently does a full retrieval + generation round trip, and `cache_hit` is always `False`.
- **Rate limiting** — a `slowapi` limiter is instantiated at application start with the configured per-minute/per-hour limits, but no route carries an `@limiter.limit(...)` decorator, so the configured limits are not currently enforced on any endpoint.

Both are flagged as concrete, well-scoped future-work items in Chapter 7 rather than treated as complete features.

### 5.8 Testing

Automated test coverage (`backend/tests/`) consists of three unit-test files (185 lines total) covering the document chunker, the language detector, and the Roman Urdu normalizer, at a mostly smoke-test level — several assertions check only that a function returns a value without raising an exception, rather than asserting the value is correct (this is noted directly in a comment inside `test_normalization.py`). There is no automated test coverage for the retrieval engine, the RAG prompt/citation logic, the LLM provider fallback chain, or the authentication/admin API routes. System-level correctness for those components is instead assessed through the end-to-end evaluation run described in Chapter 6, which exercises the full pipeline but is not a substitute for unit-level regression coverage. This gap is stated honestly in Chapter 7 rather than implied to be covered.

---

## Chapter 6: Evaluation and Results

### 6.1 Evaluation Methodology

The system was evaluated with `scripts/evaluate.py` against a 42-query benchmark (`data/test-queries/evaluation_dataset.csv`) spanning English, Roman Urdu, and mixed-language phrasings of realistic admission questions (eligibility, deadlines, required documents, fees), each labeled with the specific source documents considered ground-truth-relevant. One row is an intentionally empty query used only to exercise the pipeline's guard behavior and is excluded from scored metrics, giving 41 scored queries (38 of which carry retrieval ground truth).

For every query, the evaluation script independently runs keyword-only, semantic-only, and hybrid retrieval and scores each against the labeled relevant documents using **Recall@5**, **Recall@10**, and **Mean Reciprocal Rank (MRR)**. It then runs the full generation pipeline exactly as the production `/api/chat` endpoint would, and scores each response for:

- **Citation-marker validity** — whether every `[N]` marker in the response refers to an actual citation index (a mechanical check, not a check of factual correctness).
- **Groundedness** — an LLM-as-judge verdict (`grounded` / `partially_grounded` / `not_grounded`) produced by GPT-4o-mini, given the retrieved context and the generated response, used as an automated proxy for the human-evaluated "Answer Correctness" metric proposed in the original plan.
- **Latency** and **topic-classification accuracy** (against the keyword-based topic classifier used for admin analytics).

**A methodological caveat, stated in the evaluation script's own documentation and repeated here rather than glossed over:** the judge model (GPT-4o-mini) is a different checkpoint from, but not a fully independent vendor of, the primary answer-generating model (GPT-4o family, via the OpenAI-primary provider chain in Section 5.5) — Anthropic and Gemini keys were not reliably usable as an independent judge in this evaluation environment. This is a self-grading risk that a human-reviewed sample should offset before these numbers are treated as final; a human spot-check of the LLM judge's verdicts was **not** performed as part of this evaluation run, which is itself a limitation carried into Chapter 7. The evaluation set size (n=38–41) is also small enough that individual query outcomes move the aggregate percentages by roughly 2.5 points each, so the figures below should be read as directional rather than statistically precise.

### 6.2 Retrieval Results

| Method | Recall@5 | Recall@10 | MRR | n |
|---|---|---|---|---|
| Keyword-only | 76.3% | 84.2% | 0.701 | 38 |
| Semantic-only | 71.1% | 76.3% | 0.550 | 38 |
| **Hybrid (RRF)** | **76.3%** | **84.2%** | 0.667 | 38 |

Hybrid retrieval matches the keyword-only baseline exactly on Recall@5 and Recall@10, and clearly outperforms semantic-only retrieval on every metric. It does **not**, however, outperform keyword-only retrieval on MRR (0.667 vs. 0.701) — in this dataset, keyword search alone tends to place the single best-matching document slightly higher in the ranking than the RRF-fused result does. This is a more nuanced outcome than the literature reviewed in Chapter 2 would predict, and there is a plausible implementation-specific explanation: the keyword search deliberately uses an OR-based `to_tsquery` (Section 5.3) rather than a stricter AND-based match, which already gives it unusually strong recall for a "keyword-only" baseline, leaving less headroom for fusion with the weaker semantic channel to add value. It is also consistent with the semantic channel underperforming on its own — general-purpose embeddings (Section 5.2) with no domain- or Urdu-specific tuning are the most likely contributor, and untuned equal-weight RRF fusion (Section 5.3) may not be optimal for a corpus this small.

**Answer to Research Question 1** ("Does hybrid retrieval improve retrieval accuracy compared to vector-only search?"): **yes, clearly**, on this evaluation set. Hybrid outperforms semantic-only retrieval by 5.2 points on Recall@5, 7.9 points on Recall@10, and 0.117 on MRR. Its advantage over keyword-only retrieval specifically, however, is not supported by this data and is a result that should be reported honestly rather than assumed.

### 6.3 Generation Results

| Metric | Result |
|---|---|
| Responses evaluated (n) | 41 |
| No-answer rate | 31.7% |
| Citation-marker validity | 100% |
| Grounded / partially grounded (LLM judge) | 68.3% |
| Average latency | 3.82 s |
| P95 latency | 5.80 s |
| Topic-classification accuracy | 63.4% |

| Language | n | Success rate (grounded/partial) | Avg. latency |
|---|---|---|---|
| English | 19 | 68.4% | 4.00 s |
| Roman Urdu | 11 | 63.6% | 3.39 s |
| Mixed | 11 | 72.7% | 3.95 s |

### 6.4 Comparison Against Proposal Targets

| Metric | Target | Result | Outcome |
|---|---|---|---|
| Retrieval Recall@5 | > 80% | 76.3% | Below target |
| Citation marker validity | > 90% | 100% | **Met** |
| Average response time | < 3 s | 3.82 s | Below target |
| Roman Urdu / mixed success rate | > 70% | 68.1% (avg. of Ur/Mixed) | Below target (narrowly) |
| Answer correctness (grounded/partial, proxy) | > 75% | 68.3% | Below target |

Only citation-marker validity clearly meets its original target, and it is worth being precise about what that number actually measures: it confirms that every `[N]` marker the model emits points to a real citation slot, **not** that the cited fact is itself correctly attributed — the two other targets most analogous to "is this answer trustworthy" (grounded/partial rate, and Recall@5, which bounds how often the *correct* source document was even available to cite) both fall short. The remaining four metrics are below target, though generally by a moderate rather than a large margin (Recall@5 is 3.7 points short; the language-success average is 1.9 points short).

### 6.5 Discussion

**No-answer rate (31.7%).** Nearly a third of evaluated queries received the system's fallback "I don't have enough information" response. Cross-referencing this against Section 6.2, this is plausible given a Recall@5 in the mid-70s: when the retriever's top-5 candidates genuinely don't contain the relevant passage, the generation layer is instructed (by design, Section 5.5) to decline rather than answer from parametric knowledge — the correct behavior for hallucination avoidance, but one that surfaces retrieval gaps directly as user-visible failures rather than silently masking them with a plausible-sounding wrong answer.

**Latency (3.82 s average, 5.80 s p95).** The 0.82-second overshoot past the 3-second target is consistent with routing through an external LLM API for every request with no caching layer active (Section 5.7) — a repeated or near-duplicate query pays the full retrieval-plus-generation cost every time.

**Topic-classification accuracy (63.4%).** The topic classifier used for admin analytics is a fixed keyword-list classifier (Section 5, `topic_classifier.py`), not a component of the retrieval or generation path itself; its accuracy affects the admin dashboard's topic breakdown chart, not the answers users receive, but 63.4% suggests the keyword lists warrant expansion if the topic-breakdown analytics are to be trusted for institutional reporting.

**Answering Research Questions 2–4:**

- **RQ2 (Does query normalization enhance performance for Roman Urdu queries?)** The evaluation script normalizes Roman Urdu/mixed queries before retrieval by default (Section 5.4), so the Roman Urdu and mixed success rates reported above already reflect normalization *on*; an ablation comparing normalized vs. raw Roman Urdu input was not run in this evaluation and is a concrete, well-scoped addition for future evaluation work (Chapter 7) — the current data cannot isolate normalization's specific contribution.
- **RQ3 (Can citation grounding reduce hallucinated responses?)** Indirectly supported: 100% of emitted citation markers are structurally valid, and 68.3% of responses were judged grounded or partially grounded by the LLM judge — i.e., citation grounding did not eliminate ungrounded content (31.7% of judged responses were rated *not* grounded or partial-only), but the system prompt's citation requirement did not produce structurally broken citations either. A stronger answer to this question would require comparing against a non-cited baseline configuration, which was not run.
- **RQ4 (How effective is the system in improving access to admission information?)** The system successfully answers roughly two-thirds of realistic admission queries with a grounded, cited response across English, Roman Urdu, and mixed input — a meaningful improvement in structured access over unindexed PDF documents, but with a large enough gap (31.7% no-answer, further ungrounded responses among the rest) that it should be positioned, honestly, as a supplementary aid rather than a replacement for the admission office, consistent with the scope defined in Chapter 3.

---

## Chapter 7: Conclusion, Limitations, and Future Work

### 7.1 Conclusion

This project set out to design and implement a hybrid retrieval-based conversational assistant for University of Karachi admission policies, combining keyword and semantic search via Reciprocal Rank Fusion, citation-grounded LLM generation with multi-provider failover, and dictionary-based Roman Urdu language support, delivered through an authenticated web interface with an administrative analytics dashboard. All six secondary objectives from Chapter 3 were implemented end-to-end: a structured document knowledge base was built from official admission PDFs; a Roman Urdu normalization module was implemented and integrated into the query path; hybrid retrieval with RRF fusion is live in production; RAG-based generation with citation markers is functioning; the system was evaluated against a labeled query set; and a usable web interface, including admin analytics, was built and deployed.

The evaluation results in Chapter 6 show a working system that answers roughly two-thirds of realistic queries with a grounded, cited response, and one clear success — 100% structural citation validity — against four metrics that fall short of the proposal's original numeric targets, generally by a moderate margin. Reporting those shortfalls precisely, rather than only the successes, is itself part of this thesis's contribution: Section 6.2 in particular surfaces a genuinely interesting, counter-to-literature finding — that RRF-fused hybrid retrieval did not outperform an OR-based keyword search alone on MRR in this specific corpus — which is a more useful result for anyone extending this system than a summary that only reported the metrics that met target.

### 7.2 Limitations

- **Evaluation set size.** 38–41 scored queries is small; each query shifts aggregate percentages by roughly 2–3 points, so results should be read directionally rather than as precise estimates, and are not necessarily representative of the full space of real applicant questions.
- **Judge independence.** The automated groundedness score uses GPT-4o-mini as judge, which shares a vendor (and possibly some training lineage) with the primary answer-generation model; a human-reviewed sample was recommended by the evaluation script's own documentation but was not performed for the numbers reported in Chapter 6.
- **Untuned retrieval hyperparameters.** RRF's fusion constant and keyword/semantic weighting use standard literature defaults, not values tuned against this project's own evaluation set.
- **General-purpose embeddings.** The embedding model (Gemini `gemini-embedding-001`, with OpenAI `text-embedding-3-small` as fallback) is a general-purpose multilingual text embedding model, not one specialized for Roman Urdu or the admissions domain.
- **Incomplete operational features.** Caching and rate limiting are configured but not enforced in the current codebase (Section 5.7); production traffic is not currently protected against abuse or repeated-query cost.
- **Thin automated test coverage.** Unit tests exist only for chunking, language detection, and normalization, largely at a smoke-test level; the retrieval engine, RAG prompt construction, LLM provider failover, and auth/admin routes have no automated regression coverage (Section 5.8).
- **Topic classification.** The keyword-based topic classifier used for admin analytics reaches only 63.4% accuracy against expected topics, limiting the reliability of the dashboard's topic-breakdown chart specifically (this does not affect end-user answers, which do not depend on the topic classifier).

### 7.3 Future Work

1. **Expand and diversify the evaluation set**, ideally with a genuinely independent judge model (a different vendor from the primary answer generator) and a human-reviewed sample, as the evaluation script itself already recommends.
2. **Tune RRF and keyword/semantic weighting** against the evaluation set rather than relying on literature defaults, and re-run the keyword-vs-hybrid MRR comparison in Section 6.2 after tuning to see whether it changes the result.
3. **Wire up the already-configured caching and rate-limiting layers** — both have settings and, in caching's case, a schema column already in place, making this comparatively low-effort relative to its expected latency and abuse-resistance benefit.
4. **Add unit and integration test coverage** for retrieval, prompt/citation construction, and the LLM provider fallback chain, closing the gap identified in Section 5.8.
5. **Investigate a domain- or Roman-Urdu-adapted embedding model**, or a hybrid translation/retrieval strategy, to raise semantic-search quality specifically, since it is currently the weakest of the three retrieval configurations evaluated.
6. **Extend to Urdu script and postgraduate admissions**, and a mobile or voice interface, as originally scoped as future work in the project proposal.

---

## References

1. Lewis, P. et al., "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks," *NeurIPS*, 2020.
2. Cormack, G. V., Clarke, C. L. A., & Buettcher, S., "Reciprocal Rank Fusion Outperforms Condorcet and Individual Rank Learning Methods," *SIGIR*, 2009.
3. Robertson, S. & Zaragoza, H., "The Probabilistic Relevance Framework: BM25 and Beyond," *Foundations and Trends in Information Retrieval*, 2009.
4. Rahman, M. et al., "Challenges in Roman Urdu Text Processing: A Survey," (representative survey of Roman Urdu NLP challenges — spelling variation, code-mixing).
5. PostgreSQL Global Development Group, "Full Text Search," *PostgreSQL Documentation*.
6. pgvector Contributors, "pgvector: Open-source vector similarity search for Postgres," GitHub, 2023.
7. Google DeepMind, "Gemini Embedding Model Documentation," Google AI for Developers.
8. OpenAI, "text-embedding-3-small Model Card," OpenAI Documentation.
9. Kusupati, A. et al., "Matryoshka Representation Learning," *NeurIPS*, 2022.
10. FastAPI, Next.js, SQLAlchemy, Alembic — official project documentation (implementation references).

*(Citations 4 and 10 are placeholders for specific papers/editions to be finalized before submission — replace with the exact sources consulted during the literature review.)*

---

## Appendix A: Evaluation Dataset Sample

Representative rows from `data/test-queries/evaluation_dataset.csv` (42 rows total, English/Roman Urdu/mixed, each labeled with ground-truth relevant source documents):

| Query | Expected language | Expected topic | Relevant documents |
|---|---|---|---|
| What are the eligibility criteria for undergraduate admission? | en | eligibility | morningpro2026; eveningpro2026; self-fee-schedule; 1ST-YEAR-SELF-FINANCED-2026 |
| When is the last date for form submission? | en | deadlines | adschedule2026; admissionformsubguideline2026 |
| What documents are required for admission? | en | documents | morningpro2026; eveningpro2026; admissionformsubguideline2026 |
| How much is the admission fee? | en | fees | feesguideline2026; self-fee-schedule; 1ST-YEAR-SELF-FINANCED-2026; morningpro2026 |

## Appendix B: API Reference

**`POST /api/chat`**
```
Request:  { query: string, top_k?: number = 25, use_hybrid?: boolean = true, stream?: boolean = false }
Response: { response: string,
            citations: [{ index, document_title, section_header, page_start, page_end, content_preview }],
            latency_ms: number, llm_provider: string, cache_hit: boolean, language: string }
```

**Documents:** `GET /api/documents`, `POST /api/documents/upload` (admin), `DELETE /api/documents/{id}` (admin), `POST /api/documents/{id}/reindex` (admin), `GET /api/documents/stats`

**Auth:** `POST /api/auth/register`, `POST /api/auth/login`, `GET /api/auth/me`, `POST /api/auth/forgot-password`, `POST /api/auth/reset-password`

**Admin analytics:** `GET /api/admin/analytics/{overview|queries|languages|topics|performance|top-queries}`, `GET /api/admin/users` — all accept `?days=N` (1–365, default 30), all require an admin-role JWT.

**Health:** `GET /api/health`, `GET /api/health/db`, `GET /api/health/llm`, `GET /api/health/query-stats?hours=24`
