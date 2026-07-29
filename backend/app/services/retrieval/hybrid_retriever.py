"""
Hybrid Retrieval Engine

Combines keyword-based (BM25-style) and semantic vector search
using Reciprocal Rank Fusion (RRF) for optimal retrieval.
"""
import re
from typing import List, Tuple, Dict, Optional
from sqlalchemy import text, func
from sqlalchemy.orm import Session

from app.models import Chunk, Document
from .embeddings import get_embedding_model


class HybridRetriever:
    """
    Hybrid retrieval combining keyword and semantic search.
    
    Uses Reciprocal Rank Fusion (RRF) to merge results from:
    1. PostgreSQL full-text search (keyword/BM25-style)
    2. Vector similarity search (semantic)
    """
    
    def __init__(
        self,
        top_k: int = 20,
        rrf_k: int = 60,
        keyword_weight: float = 0.5,
        semantic_weight: float = 0.5
    ):
        """
        Initialize the hybrid retriever.
        
        Args:
            top_k: Number of results to return after fusion
            rrf_k: RRF constant (higher = more weight to rank position)
            keyword_weight: Weight for keyword search scores
            semantic_weight: Weight for semantic search scores
        """
        self.top_k = top_k
        self.rrf_k = rrf_k
        self.keyword_weight = keyword_weight
        self.semantic_weight = semantic_weight
        self.embedding_model = get_embedding_model()
    
    def retrieve(
        self,
        query: str,
        db: Session,
        top_k: Optional[int] = None,
        use_hybrid: bool = True
    ) -> List[Tuple[Chunk, float, Dict]]:
        """
        Retrieve relevant chunks for a query.
        
        Args:
            query: Search query
            db: Database session
            top_k: Override default top_k
            use_hybrid: Use hybrid search (True) or semantic-only (False)
            
        Returns:
            List of tuples: (Chunk, score, metadata)
        """
        top_k = top_k or self.top_k
        
        if use_hybrid:
            # Get both keyword and semantic results
            keyword_results = self._keyword_search(query, db, top_k=top_k * 2)
            semantic_results = self._semantic_search(query, db, top_k=top_k * 2)
            
            # Fuse results using RRF
            fused_results = self._reciprocal_rank_fusion(
                keyword_results,
                semantic_results,
                top_k=top_k
            )
        else:
            # Semantic-only search
            semantic_results = self._semantic_search(query, db, top_k=top_k)
            fused_results = [
                (chunk, score, {"source": "semantic", "rank": i + 1})
                for i, (chunk, score) in enumerate(semantic_results)
            ]
        
        return fused_results
    
    def _keyword_search(
        self,
        query: str,
        db: Session,
        top_k: int = 40
    ) -> List[Tuple[Chunk, float]]:
        """
        Perform keyword-based full-text search using PostgreSQL FTS.

        Terms are OR-matched (any term can hit) and ranked by ts_rank, which
        favors chunks matching more terms - plainto_tsquery ANDs every term,
        which made keyword search return nothing unless a chunk happened to
        contain every single word of a multi-word natural-language query.
        """
        search_terms = [re.sub(r'\W', '', t) for t in query.split() if len(t) > 2]
        search_terms = [t for t in search_terms if t]
        if not search_terms:
            return []

        tsquery = func.to_tsquery('english', ' | '.join(search_terms))
        results = db.query(
            Chunk,
            func.ts_rank(
                func.to_tsvector('english', Chunk.content),
                tsquery
            ).label('score')
        ).filter(
            func.to_tsvector('english', Chunk.content).op('@@')(tsquery)
        ).order_by(text('score DESC')).limit(top_k).all()
        return [(chunk, float(score)) for chunk, score in results]

    def _semantic_search(
        self,
        query: str,
        db: Session,
        top_k: int = 40
    ) -> List[Tuple[Chunk, float]]:
        """Perform semantic vector similarity search using pgvector cosine distance."""
        query_embedding = self.embedding_model.encode_query(query)

        distance = Chunk.embedding.cosine_distance(query_embedding)
        results = db.query(Chunk, distance.label('distance')).filter(
            Chunk.embedding.isnot(None)
        ).order_by(distance).limit(top_k).all()

        return [(chunk, 1.0 - float(dist)) for chunk, dist in results]
    
    def _reciprocal_rank_fusion(
        self,
        keyword_results: List[Tuple[Chunk, float]],
        semantic_results: List[Tuple[Chunk, float]],
        top_k: int
    ) -> List[Tuple[Chunk, float, Dict]]:
        """
        Fuse results from keyword and semantic search using RRF.
        
        RRF Formula: score = sum(1 / (k + rank)) for each result
        
        Args:
            keyword_results: Results from keyword search
            semantic_results: Results from semantic search
            top_k: Number of final results to return
            
        Returns:
            Fused and re-ranked results with metadata
        """
        # Track scores and ranks for each chunk
        chunk_scores: Dict[str, float] = {}
        chunk_metadata: Dict[str, Dict] = {}
        chunk_map: Dict[str, Chunk] = {}
        
        # Score keyword results
        for rank, (chunk, score) in enumerate(keyword_results):
            chunk_id = str(chunk.id)
            rrf_score = 1.0 / (self.rrf_k + rank + 1)
            
            if chunk_id not in chunk_scores:
                chunk_scores[chunk_id] = 0
                chunk_metadata[chunk_id] = {
                    "keyword_rank": rank + 1,
                    "keyword_score": score,
                    "source": "hybrid"
                }
                chunk_map[chunk_id] = chunk
            
            chunk_scores[chunk_id] += self.keyword_weight * rrf_score
            chunk_metadata[chunk_id]["rrf_score"] = chunk_scores[chunk_id]
        
        # Score semantic results
        for rank, (chunk, score) in enumerate(semantic_results):
            chunk_id = str(chunk.id)
            rrf_score = 1.0 / (self.rrf_k + rank + 1)
            
            if chunk_id not in chunk_scores:
                chunk_scores[chunk_id] = 0
                chunk_metadata[chunk_id] = {
                    "semantic_rank": rank + 1,
                    "semantic_score": score,
                    "source": "hybrid"
                }
                chunk_map[chunk_id] = chunk
            else:
                chunk_metadata[chunk_id]["semantic_rank"] = rank + 1
                chunk_metadata[chunk_id]["semantic_score"] = score
            
            chunk_scores[chunk_id] += self.semantic_weight * rrf_score
            chunk_metadata[chunk_id]["rrf_score"] = chunk_scores[chunk_id]
        
        # Sort by fused score
        sorted_chunks = sorted(
            chunk_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )[:top_k]
        
        # Build final results
        final_results = []
        for final_rank, (chunk_id, score) in enumerate(sorted_chunks):
            chunk = chunk_map[chunk_id]
            metadata = chunk_metadata[chunk_id]
            metadata["final_rank"] = final_rank + 1
            metadata["final_score"] = score
            
            final_results.append((chunk, score, metadata))
        
        return final_results


def get_retriever() -> HybridRetriever:
    """Get a configured hybrid retriever instance."""
    from app.core.config import settings

    return HybridRetriever(
        top_k=settings.RETRIEVAL_TOP_K,
        rrf_k=settings.RRF_K,
        keyword_weight=settings.RRF_WEIGHT_KEYWORD,
        semantic_weight=settings.RRF_WEIGHT_SEMANTIC
    )
