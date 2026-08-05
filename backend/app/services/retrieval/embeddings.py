"""
Embedding Model Module

Generates vector embeddings for semantic search via OpenAI text-embedding-3-small (1536-dim).
"""
from typing import List, Optional
import numpy as np
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingModel:
    """OpenAI embedding wrapper."""

    def __init__(self):
        self._openai_client = None

    def _get_openai_client(self):
        if self._openai_client is None:
            from openai import OpenAI
            self._openai_client = OpenAI(api_key=settings.OPENAI_API_KEY or "", timeout=30.0)
        return self._openai_client

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
        logger.debug("Embedding %d texts via OpenAI", len(texts))
        embeddings = self._openai_embed_batch(texts, batch_size)

        if show_progress:
            print(f"Embedded {len(texts)} texts")
        return np.array(embeddings)

    def encode_query(self, text: str) -> np.ndarray:
        """Generate embedding for a single query."""
        return np.array(self._openai_embed_one(text))

    def get_dimension(self) -> int:
        """Return the embedding dimension for the active provider."""
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
