"""
Chat API Endpoints

Handles user queries with RAG-based response generation.
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List, Dict
from dataclasses import dataclass
import anyio
import anyio.to_thread
import time
import json
import logging

from ..core.database import get_db, SessionLocal
from ..core.config import settings
from ..core import cache
from ..core.ratelimit import limiter, CHAT_RATE_LIMIT
from ..core.security import get_current_user
from ..models import QueryLog
from ..services.roman_urdu import LanguageDetector, RomanUrduNormalizer
from ..services.retrieval.hybrid_retriever import (
    get_retriever, is_aggregation_query, BROAD_CHUNK_BUDGET,
)
from ..services.rag.llm_provider import get_llm_provider
from ..services.rag.prompt import create_rag_prompt
from ..services.analytics.topic_classifier import classify as classify_topic

router = APIRouter()
logger = logging.getLogger(__name__)


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    query: str
    # Retrieval pulls top_k*2 from each of the keyword and semantic arms, and
    # the prompt builder then keeps only max_chunks (10). At 25 this fetched
    # ~100 full chunk bodies from Neon to discard 90% of them.
    top_k: Optional[int] = 10
    use_hybrid: Optional[bool] = True
    stream: Optional[bool] = False


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    response: str
    citations: List[Dict]
    latency_ms: int
    llm_provider: str
    cache_hit: bool = False
    language: str = "en"


class CitationInfo(BaseModel):
    """Citation information."""
    index: int
    document_title: str
    section_header: str
    page_start: int
    page_end: int
    content_preview: str


# Initialize services
language_detector = LanguageDetector()
normalizer = RomanUrduNormalizer(use_translation=False)


@dataclass
class _RagContext:
    """Everything the retrieval half of a chat request produces."""
    language: str
    normalized_query: str
    is_broad: bool
    chunks: List
    citations: List
    system_prompt: str
    user_prompt: str
    retrieval_scores: Dict[str, float]
    max_tokens: int


def _build_rag_context(query: str, db: Session, chat_request: "ChatRequest") -> Optional[_RagContext]:
    """
    Detect language, retrieve chunks and build the prompt for a query.

    Shared by /chat and /chat/stream so the two cannot drift apart - the
    streaming endpoint had already lost the aggregation-query handling and the
    chunk budget that /chat gained. Returns None when nothing was retrieved.

    Every call in here is blocking, synchronous I/O; async callers must run it
    in a worker thread.
    """
    language, _ = language_detector.detect(query)
    normalized_query = normalizer.normalize(query) if language in ('ur', 'mixed') else query

    # Count/enumeration questions ("how many teachers", "list all departments")
    # need many more chunks than a normal lookup - the answer is scattered
    # across a document, not concentrated in the usual top-5/10.
    is_broad = is_aggregation_query(normalized_query)
    retriever = get_retriever()
    results = retriever.retrieve(
        query=normalized_query,
        db=db,
        top_k=chat_request.top_k,
        use_hybrid=chat_request.use_hybrid,
        broad=is_broad,
    )
    if not results:
        return None

    chunks = [chunk for chunk, score, meta in results]
    retrieval_scores = {str(chunk.id): float(score) for chunk, score, meta in results}

    # Build document title map.
    # One query for the distinct documents, not one per chunk: the retrieved
    # chunks routinely come from a handful of documents (25 chunks spanned 4
    # documents in practice), and each per-chunk lookup was a full round trip
    # to Neon.
    from ..models import Document
    doc_ids = {chunk.doc_id for chunk in chunks}
    documents = {
        str(doc_id): title
        for doc_id, title in db.query(Document.id, Document.title).filter(
            Document.id.in_(doc_ids)
        )
    }

    system_prompt, user_prompt, citations = create_rag_prompt(
        query=query,
        chunks=chunks,
        documents=documents,
        # Same constant the broad retrieval path used, so the prompt cap and
        # the retrieval budget cannot drift apart - they were 40 and 76.
        max_chunks=BROAD_CHUNK_BUDGET if is_broad else 10,
        # So Roman Urdu / code-mixed queries are answered in kind instead of
        # always in English.
        language=language,
    )

    return _RagContext(
        language=language,
        normalized_query=normalized_query,
        is_broad=is_broad,
        chunks=chunks,
        citations=citations,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        retrieval_scores=retrieval_scores,
        max_tokens=2048 if is_broad else settings.LLM_MAX_TOKENS,
    )


def _format_citations(citations: List, chunks: List) -> List[Dict]:
    """Attach a content preview to each citation the prompt builder produced."""
    out = []
    for citation in citations:
        chunk_idx = citation.chunk_index - 1
        if chunk_idx < len(chunks):
            content = chunks[chunk_idx].content
            preview = content[:150] + "..." if len(content) > 150 else content
        else:
            preview = ""
        out.append(CitationInfo(
            index=citation.chunk_index,
            document_title=citation.document_title,
            section_header=citation.section_header,
            page_start=citation.page_start,
            page_end=citation.page_end,
            content_preview=preview,
        ).dict())
    return out


def _log_query(db: Session, *, query: str, ctx: _RagContext, response_text: str,
               latency_ms: int, provider_name: str, user_id,
               cache_hit: bool = False) -> None:
    """Record a query for analytics. Never fails the request."""
    try:
        db.add(QueryLog(
            query_text=query,
            detected_language=ctx.language,
            normalized_query=ctx.normalized_query,
            response=response_text,
            latency_ms=latency_ms,
            cache_hit=cache_hit,
            llm_provider=provider_name,
            retrieval_scores=json.dumps(ctx.retrieval_scores),
            topic=classify_topic(ctx.normalized_query),
            user_id=user_id,
        ))
        db.commit()
    except Exception as e:
        db.rollback()
        logger.warning(f"Failed to log query: {e}")


def _log_cache_hit(db: Session, *, query: str, cached: dict, latency_ms: int, user_id) -> None:
    """Record a cache-served query so analytics still counts it. Never fails the request."""
    try:
        db.add(QueryLog(
            query_text=query,
            detected_language=cached.get("language"),
            normalized_query=cached.get("normalized_query"),
            response=cached.get("response"),
            latency_ms=latency_ms,
            cache_hit=True,
            llm_provider=cached.get("llm_provider"),
            retrieval_scores=None,
            topic=cached.get("topic"),
            user_id=user_id,
        ))
        db.commit()
    except Exception as e:
        db.rollback()
        logger.warning(f"Failed to log cache hit: {e}")


@router.post("/chat", response_model=ChatResponse)
@limiter.limit(CHAT_RATE_LIMIT)
def chat(
    request: Request,
    payload: ChatRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Process a user query and generate a RAG-based response.

    Deliberately a sync `def`: retrieval, embedding and every database call
    below are blocking, synchronous I/O. Declared `async`, they ran directly on
    the event loop and serialized all concurrent requests behind each other.
    FastAPI runs a sync endpoint in a worker thread instead.

    This endpoint:
    1. Detects query language (English/Roman Urdu)
    2. Normalizes Roman Urdu queries
    3. Retrieves relevant document chunks
    4. Generates response using LLM
    5. Logs query for analytics
    """
    start_time = time.time()

    query = payload.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    user_id = current_user.id if current_user else None

    # Serve an identical prior answer from Redis without touching retrieval or
    # the LLM. Key covers the retrieval knobs so a different top_k / hybrid
    # flag is a different entry.
    cache_key = cache.make_key(query, payload.top_k, payload.use_hybrid)
    cached = cache.get_cached(cache_key)
    if cached:
        latency_ms = int((time.time() - start_time) * 1000)
        _log_cache_hit(db, query=query, cached=cached, latency_ms=latency_ms, user_id=user_id)
        return ChatResponse(
            response=cached["response"],
            citations=cached["citations"],
            latency_ms=latency_ms,
            llm_provider=cached["llm_provider"],
            cache_hit=True,
            language=cached["language"],
        )

    # Steps 1-5: language detection, normalization, retrieval, prompt build
    ctx = _build_rag_context(query, db, payload)
    if ctx is None:
        language, _ = language_detector.detect(query)
        return ChatResponse(
            response="I couldn't find relevant information about this in the admission documents. Please try rephrasing your question or contact the admission office directly.",
            citations=[],
            latency_ms=int((time.time() - start_time) * 1000),
            llm_provider="none",
            language=language
        )

    # Step 6: Generate response using LLM
    llm_provider = get_llm_provider()
    # Provisional: overwritten below with whichever provider actually answered.
    # Reading it only before the call reported "openai" even when OpenAI had
    # failed and Gemini served the response, which made both the API response
    # and the analytics in query_logs wrong.
    provider_name = llm_provider.get_current_provider()

    try:
        # The provider interface is async but this endpoint is sync (see
        # docstring), so run the coroutine to completion on a loop of its own in
        # this worker thread. The generate() call is the request's longest wait,
        # and blocking a worker thread for it - rather than the event loop -
        # is the whole point of the sync endpoint.
        response_text, provider_name = anyio.run(
            lambda: llm_provider.generate_with_provider(
                prompt=ctx.user_prompt,
                system_prompt=ctx.system_prompt,
                temperature=settings.LLM_TEMPERATURE,
                max_tokens=ctx.max_tokens,
            )
        )
    except Exception as e:
        # Fallback: return retrieved chunks directly
        response_text = "I found relevant information but couldn't generate a response. Here are the relevant excerpts:\n\n"
        for i, chunk in enumerate(ctx.chunks[:3], 1):
            response_text += f"{i}. {chunk.content[:200]}...\n\n"
        provider_name = "fallback"
    
    # Step 7: Format citations
    citation_list = _format_citations(ctx.citations, ctx.chunks)

    latency_ms = int((time.time() - start_time) * 1000)

    # Cache successful, model-generated answers only. "none"/"fallback" mean the
    # answer is a placeholder or raw excerpts - not worth replaying for a day.
    if provider_name not in ("none", "fallback"):
        cache.set_cached(cache_key, {
            "response": response_text,
            "citations": citation_list,
            "language": ctx.language,
            "llm_provider": provider_name,
            "normalized_query": ctx.normalized_query,
            "topic": classify_topic(ctx.normalized_query),
        })

    # Step 8: Log query for analytics
    _log_query(
        db,
        query=query,
        ctx=ctx,
        response_text=response_text,
        latency_ms=latency_ms,
        provider_name=provider_name,
        user_id=user_id,
    )

    return ChatResponse(
        response=response_text,
        citations=citation_list,
        latency_ms=latency_ms,
        llm_provider=provider_name,
        cache_hit=False,
        language=ctx.language
    )


@router.post("/chat/stream")
@limiter.limit(CHAT_RATE_LIMIT)
async def chat_stream(
    request: Request,
    payload: ChatRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Streaming chat endpoint. Same retrieval and prompt as /chat, delivered as
    Server-Sent Events so the answer appears as it is generated.

    Each event carries a JSON object with a "type":

        meta   once, before any text - language and citations
        token  a fragment of the answer, in "text"
        done   once, at the end - final latency and serving provider
        error  generation failed; "message" is safe to show a user

    JSON rather than raw text in the SSE `data:` field: SSE terminates an event
    at a blank line, so a model answer containing a newline - a list, a
    paragraph break - was being split across events and silently truncated by
    the client. It also removes the ambiguity of a literal "[DONE]" appearing
    in an answer.
    """
    query = payload.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    start_time = time.time()
    user_id = current_user.id if current_user else None

    def event(data: Dict) -> str:
        return f"data: {json.dumps(data)}\n\n"

    # Replay a cached answer as a single token event rather than re-streaming
    # it from the model.
    cache_key = cache.make_key(query, payload.top_k, payload.use_hybrid)
    cached = cache.get_cached(cache_key)
    if cached:
        latency_ms = int((time.time() - start_time) * 1000)
        _log_cache_hit(db, query=query, cached=cached, latency_ms=latency_ms, user_id=user_id)

        async def replay():
            yield event({
                "type": "meta",
                "language": cached["language"],
                "citations": cached["citations"],
            })
            yield event({"type": "token", "text": cached["response"]})
            yield event({
                "type": "done",
                "latency_ms": latency_ms,
                "llm_provider": cached["llm_provider"],
                "cache_hit": True,
            })

        return StreamingResponse(replay(), media_type="text/event-stream")

    # Retrieval, embedding and the database calls behind them are blocking and
    # this endpoint is async, so they go to a worker thread rather than
    # stalling the event loop for every other request in flight.
    ctx = await anyio.to_thread.run_sync(_build_rag_context, query, db, payload)

    if ctx is None:
        language, _ = language_detector.detect(query)

        async def empty():
            yield event({"type": "meta", "language": language, "citations": []})
            yield event({
                "type": "token",
                "text": "I couldn't find relevant information about this in the "
                        "admission documents. Please try rephrasing your question "
                        "or contact the admission office directly.",
            })
            yield event({
                "type": "done",
                "latency_ms": int((time.time() - start_time) * 1000),
                "llm_provider": "none",
            })

        return StreamingResponse(empty(), media_type="text/event-stream")

    async def generate():
        llm_provider = get_llm_provider()
        provider_name = llm_provider.get_current_provider()
        parts = []

        yield event({
            "type": "meta",
            "language": ctx.language,
            "citations": _format_citations(ctx.citations, ctx.chunks),
        })

        try:
            async for chunk, served_by in llm_provider.stream_with_provider(
                prompt=ctx.user_prompt,
                system_prompt=ctx.system_prompt,
                temperature=settings.LLM_TEMPERATURE,
                max_tokens=ctx.max_tokens,
            ):
                provider_name = served_by
                parts.append(chunk)
                yield event({"type": "token", "text": chunk})
        except Exception as e:
            # The provider's own error text is not shown to the user - it can
            # carry request ids and key fragments.
            logger.error(f"Streaming generation failed: {e}")
            provider_name = "error"
            yield event({
                "type": "error",
                "message": "The response could not be completed. Please try again.",
            })

        latency_ms = int((time.time() - start_time) * 1000)
        yield event({
            "type": "done",
            "latency_ms": latency_ms,
            "llm_provider": provider_name,
        })

        answer = "".join(parts)

        # Cache only a complete, model-generated answer.
        if answer and provider_name not in ("none", "fallback", "error"):
            cache.set_cached(cache_key, {
                "response": answer,
                "citations": _format_citations(ctx.citations, ctx.chunks),
                "language": ctx.language,
                "llm_provider": provider_name,
                "normalized_query": ctx.normalized_query,
                "topic": classify_topic(ctx.normalized_query),
            })

        # Log on a session of this generator's own. The request-scoped session
        # from Depends(get_db) is closed once the endpoint returns, which for a
        # StreamingResponse happens before a single token has been generated.
        log_db = SessionLocal()
        try:
            await anyio.to_thread.run_sync(
                lambda: _log_query(
                    log_db,
                    query=query,
                    ctx=ctx,
                    response_text=answer,
                    latency_ms=latency_ms,
                    provider_name=provider_name,
                    user_id=user_id,
                )
            )
        finally:
            log_db.close()

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.get("/chat/suggestions")
async def get_suggestions(
    limit: int = 5,
    db: Session = Depends(get_db)
):
    """
    Get suggested queries based on recent popular queries.
    """
    # Get recent queries from logs
    recent = db.query(QueryLog).order_by(
        QueryLog.created_at.desc()
    ).limit(limit * 2).all()
    
    # Extract unique queries (simplified)
    suggestions = []
    seen = set()
    for log in recent:
        if log.query_text not in seen and len(log.query_text) < 100:
            suggestions.append(log.query_text)
            seen.add(log.query_text)
        if len(suggestions) >= limit:
            break
    
    return {"suggestions": suggestions}
