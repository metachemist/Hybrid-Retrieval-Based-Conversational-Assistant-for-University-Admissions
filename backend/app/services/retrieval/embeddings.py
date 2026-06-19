"""
Embedding Model Module

Generates vector embeddings for semantic search.
Primary: Gemini gemini-embedding-001 (free tier, 768-dim)
Fallback: OpenAI text-embedding-3-small (1536-dim)
"""
from typing import List, Optional
import numpy as np
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingModel:
    """Embedding wrapper — uses Gemini if available, falls back to OpenAI."""

    def __init__(self):
        self._gemini_client = None
        self._openai_client = None

    # ------------------------------------------------------------------
    # Provider selection
    # ------------------------------------------------------------------

    def _use_gemini(self) -> bool:
        return bool(settings.GEMINI_API_KEY)

    def _get_gemini_client(self):
        if self._gemini_client is None:
            from google import genai
            self._gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)
        return self._gemini_client

    def _get_openai_client(self):
        if self._openai_client is None:
            from openai import OpenAI
            self._openai_client = OpenAI(api_key=settings.OPENAI_API_KEY or "")
        return self._openai_client

    # ------------------------------------------------------------------
    # Gemini embeddings (gemini-embedding-001, 768-dim, free)
    # ------------------------------------------------------------------

    def _gemini_embed_batch(self, texts: List[str]) -> List[List[float]]:
        client = self._get_gemini_client()
        results = []
        for text in texts:
            resp = client.models.embed_content(
                model="gemini-embedding-001",
                contents=text,
            )
            results.append(resp.embeddings[0].values)
        return results

    def _gemini_embed_one(self, text: str) -> List[float]:
        client = self._get_gemini_client()
        resp = client.models.embed_content(
            model="gemini-embedding-001",
            contents=text,
        )
        return resp.embeddings[0].values

    # ------------------------------------------------------------------
    # OpenAI embeddings (text-embedding-3-small, 1536-dim)
    # ------------------------------------------------------------------

    def _openai_embed_batch(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        client = self._get_openai_client()
        all_embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            resp = client.embeddings.create(model=settings.EMBEDDING_MODEL, input=batch)
            all_embeddings.extend([item.embedding for item in resp.data])
        return all_embeddings

    def _openai_embed_one(self, text: str) -> List[float]:
        client = self._get_openai_client()
        resp = client.embeddings.create(model=settings.EMBEDDING_MODEL, input=text)
        return resp.data[0].embedding

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def encode(self, texts: List[str], batch_size: int = 32, show_progress: bool = False) -> np.ndarray:
        """Generate embeddings for a list of texts."""
        if self._use_gemini():
            logger.debug("Embedding %d texts via Gemini", len(texts))
            embeddings = self._gemini_embed_batch(texts)
        else:
            logger.debug("Embedding %d texts via OpenAI", len(texts))
            embeddings = self._openai_embed_batch(texts, batch_size)

        if show_progress:
            print(f"Embedded {len(texts)} texts")
        return np.array(embeddings)

    def encode_query(self, text: str) -> np.ndarray:
        """Generate embedding for a single query."""
        if self._use_gemini():
            return np.array(self._gemini_embed_one(text))
        else:
            return np.array(self._openai_embed_one(text))

    def get_dimension(self) -> int:
        """Return the embedding dimension for the active provider."""
        if self._use_gemini():
            return 768
        return settings.EMBEDDING_DIMENSION


# Singleton
_embedding_model: Optional[EmbeddingModel] = None


def get_embedding_model() -> EmbeddingModel:
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = EmbeddingModel()
    return _embedding_model


def initialize_model():
    get_embedding_model()
