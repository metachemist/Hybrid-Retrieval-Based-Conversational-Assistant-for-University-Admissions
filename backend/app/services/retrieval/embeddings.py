"""
Embedding Model Module

Generates vector embeddings for semantic search via Google
gemini-embedding-001 (output_dimensionality=768).

Two task types are used, as recommended by Google:
- RETRIEVAL_DOCUMENT  for chunk text stored in the index (encode / encode_documents)
- RETRIEVAL_QUERY      for the user's question at search time (encode_query)

Output dimensions below the native 3072 are returned un-normalised, so every
vector is L2-normalised here. With unit vectors, cosine distance and dot
product agree, which is what the HNSW `vector_cosine_ops` index expects.
"""
from typing import List, Optional
import logging

import numpy as np

from app.core.config import settings

logger = logging.getLogger(__name__)

_DOC_TASK = "RETRIEVAL_DOCUMENT"
_QUERY_TASK = "RETRIEVAL_QUERY"


def _l2_normalize(vec: np.ndarray) -> np.ndarray:
    """Scale a vector (or each row of a matrix) to unit L2 norm."""
    vec = np.asarray(vec, dtype=np.float32)
    if vec.ndim == 1:
        norm = np.linalg.norm(vec)
        return vec / norm if norm > 0 else vec
    norms = np.linalg.norm(vec, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return vec / norms


class EmbeddingModel:
    """Google Gemini embedding wrapper."""

    def __init__(self):
        self._client = None

    def _get_client(self):
        if self._client is None:
            from google import genai
            from google.genai import types
            self._client = genai.Client(
                api_key=settings.GEMINI_API_KEY or "",
                http_options=types.HttpOptions(timeout=60_000),
            )
        return self._client

    def _embed(self, texts: List[str], task_type: str, batch_size: int = 100) -> np.ndarray:
        """Embed a list of texts for the given task type, batching API calls."""
        from google.genai import types

        client = self._get_client()
        config = types.EmbedContentConfig(
            task_type=task_type,
            output_dimensionality=settings.EMBEDDING_DIMENSION,
        )

        vectors: List[List[float]] = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            resp = client.models.embed_content(
                model=settings.EMBEDDING_MODEL,
                contents=batch,
                config=config,
            )
            vectors.extend(e.values for e in resp.embeddings)

        return _l2_normalize(np.array(vectors, dtype=np.float32))

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def encode(self, texts: List[str], batch_size: int = 100, show_progress: bool = False) -> np.ndarray:
        """Embed document/chunk text (RETRIEVAL_DOCUMENT task)."""
        logger.debug("Embedding %d documents via %s", len(texts), settings.EMBEDDING_MODEL)
        embeddings = self._embed(texts, _DOC_TASK, batch_size)
        if show_progress:
            print(f"Embedded {len(texts)} texts")
        return embeddings

    # Alias kept explicit so ingestion call sites read clearly.
    encode_documents = encode

    def encode_query(self, text: str) -> np.ndarray:
        """Embed a single search query (RETRIEVAL_QUERY task)."""
        return self._embed([text], _QUERY_TASK)[0]

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
