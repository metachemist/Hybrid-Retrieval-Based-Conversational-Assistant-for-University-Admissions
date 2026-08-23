"""
Chat API Endpoints

Handles user queries with RAG-based response generation.
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List, Dict
import anyio
import time
import json

from ..core.database import get_db
from ..core.config import settings
from ..core.security import get_current_user
from ..models import QueryLog
from ..services.roman_urdu import LanguageDetector, RomanUrduNormalizer
from ..services.retrieval.hybrid_retriever import get_retriever, is_aggregation_query
from ..services.retrieval.embeddings import get_embedding_model
from ..services.rag.llm_provider import get_llm_provider
from ..services.rag.prompt import create_rag_prompt, RAGPromptBuilder
from ..services.analytics.topic_classifier import classify as classify_topic

router = APIRouter()


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


@router.post("/chat", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    client_request: Request = None,
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
    
    query = request.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    # Step 1: Language detection
    language, lang_confidence = language_detector.detect(query)
    
    # Step 2: Query normalization (for Roman Urdu)
    normalized_query = query
    if language in ('ur', 'mixed'):
        normalized_query = normalizer.normalize(query)
    
    # Step 3: Check cache (optional - implement Redis caching)
    # cache_key = f"query:{normalized_query}"
    # cached_response = await cache.get(cache_key)
    # if cached_response:
    #     return ChatResponse(**cached_response, cache_hit=True)
    
    # Step 4: Retrieve relevant chunks
    # Count/enumeration questions ("how many teachers", "list all departments")
    # need many more chunks than a normal lookup - the answer is scattered
    # across a document, not concentrated in the usual top-5/10.
    is_broad = is_aggregation_query(normalized_query)
    retriever = get_retriever()
    results = retriever.retrieve(
        query=normalized_query,
        db=db,
        top_k=request.top_k,
        use_hybrid=request.use_hybrid,
        broad=is_broad
    )

    if not results:
        # No relevant chunks found
        return ChatResponse(
            response="I couldn't find relevant information about this in the admission documents. Please try rephrasing your question or contact the admission office directly.",
            citations=[],
            latency_ms=int((time.time() - start_time) * 1000),
            llm_provider="none",
            language=language
        )
    
    # Extract chunks and build document map
    chunks = [chunk for chunk, score, meta in results]
    retrieval_scores = {str(chunk.id): float(score) for chunk, score, meta in results}
    
    # Build document title map.
    # One query for the distinct documents, not one per chunk: the retrieved
    # chunks routinely come from a handful of documents (25 chunks spanned 4
    # documents in practice), and each per-chunk lookup was a full round trip
    # to Neon.
    from ..models import Document
    doc_ids = {chunk.doc_id for chunk, score, meta in results}
    documents = {
        str(doc_id): title
        for doc_id, title in db.query(Document.id, Document.title).filter(
            Document.id.in_(doc_ids)
        )
    }
    
    # Step 5: Build RAG prompt
    system_prompt, user_prompt, citations = create_rag_prompt(
        query=query,
        chunks=chunks,
        documents=documents,
        max_chunks=40 if is_broad else 10
    )
    
    # Step 6: Generate response using LLM
    llm_provider = get_llm_provider()
    provider_name = llm_provider.get_current_provider()
    
    try:
        # The provider interface is async but this endpoint is sync (see
        # docstring), so run the coroutine to completion on a loop of its own in
        # this worker thread. The generate() call is the request's longest wait,
        # and blocking a worker thread for it - rather than the event loop -
        # is the whole point of the sync endpoint.
        response_text = anyio.run(
            lambda: llm_provider.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=settings.LLM_TEMPERATURE,
                max_tokens=2048 if is_broad else settings.LLM_MAX_TOKENS,
            )
        )
    except Exception as e:
        # Fallback: return retrieved chunks directly
        response_text = "I found relevant information but couldn't generate a response. Here are the relevant excerpts:\n\n"
        for i, chunk in enumerate(chunks[:3], 1):
            response_text += f"{i}. {chunk.content[:200]}...\n\n"
        provider_name = "fallback"
    
    # Step 7: Format citations
    citation_list = []
    builder = RAGPromptBuilder()
    for citation in citations:
        # Find corresponding chunk for content preview
        chunk_idx = citation.chunk_index - 1
        if chunk_idx < len(chunks):
            preview = chunks[chunk_idx].content[:150] + "..." if len(chunks[chunk_idx].content) > 150 else chunks[chunk_idx].content
        else:
            preview = ""
        
        citation_list.append(CitationInfo(
            index=citation.chunk_index,
            document_title=citation.document_title,
            section_header=citation.section_header,
            page_start=citation.page_start,
            page_end=citation.page_end,
            content_preview=preview
        ).dict())
    
    # Calculate latency
    latency_ms = int((time.time() - start_time) * 1000)
    
    # Step 8: Log query for analytics
    topic = classify_topic(normalized_query)
    try:
        query_log = QueryLog(
            query_text=query,
            detected_language=language,
            normalized_query=normalized_query,
            response=response_text,
            latency_ms=latency_ms,
            cache_hit=False,
            llm_provider=provider_name,
            retrieval_scores=json.dumps(retrieval_scores),
            topic=topic,
            user_id=current_user.id if current_user else None,
        )
        db.add(query_log)
        db.commit()
    except Exception as e:
        # Don't fail the request if logging fails
        db.rollback()
        print(f"Failed to log query: {e}")
    
    return ChatResponse(
        response=response_text,
        citations=citation_list,
        latency_ms=latency_ms,
        llm_provider=provider_name,
        cache_hit=False,
        language=language
    )


@router.post("/chat/stream")
async def chat_stream(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """
    Streaming chat endpoint.
    
    Returns Server-Sent Events (SSE) stream of response tokens.
    """
    from fastapi.responses import StreamingResponse
    
    async def generate():
        # Similar logic to /chat but with streaming
        query = request.query.strip()
        language, _ = language_detector.detect(query)
        normalized_query = normalizer.normalize(query) if language in ('ur', 'mixed') else query
        
        retriever = get_retriever()
        results = retriever.retrieve(query=normalized_query, db=db, top_k=request.top_k)
        
        if not results:
            yield "data: I couldn't find relevant information.\n\n"
            return
        
        from ..models import Document as DocumentModel
        chunks = [chunk for chunk, score, meta in results]
        doc_ids = {chunk.doc_id for chunk, score, meta in results}
        documents = {
            str(doc_id): title
            for doc_id, title in db.query(
                DocumentModel.id, DocumentModel.title
            ).filter(DocumentModel.id.in_(doc_ids))
        }
        
        system_prompt, user_prompt, _ = create_rag_prompt(query, chunks, documents)
        
        llm_provider = get_llm_provider()
        
        try:
            async for chunk in llm_provider.generate_stream(
                prompt=user_prompt,
                system_prompt=system_prompt
            ):
                yield f"data: {chunk}\n\n"
        except Exception as e:
            yield f"data: [Error: {str(e)}]\n\n"
        
        yield "data: [DONE]\n\n"
    
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
