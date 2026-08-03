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

# gemini-embedding-001 defaults to 3072-dim; truncated via Matryoshka
# representation learning to match the chunks.embedding column (vector(768)).
GEMINI_EMBEDDING_DIMENSION = 768


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
            from google.genai import types
            self._gemini_client = genai.Client(
                api_key=settings.GEMINI_API_KEY,
                http_options=types.HttpOptions(timeout=30_000),
            )
        return self._gemini_client

    def _get_openai_client(self):
        if self._openai_client is None:
            from openai import OpenAI
            self._openai_client = OpenAI(api_key=settings.OPENAI_API_KEY or "", timeout=30.0)
        return self._openai_client

    # ------------------------------------------------------------------
    # Gemini embeddings (gemini-embedding-001, 768-dim, free)
    # ------------------------------------------------------------------

    def _is_gemini_fallback_worthy(self, e: Exception) -> bool:
        """Quota errors (429) and transient network failures - not other bugs."""
        from google.genai import errors
        import httpx
        if isinstance(e, errors.ClientError):
            return e.code == 429
        return isinstance(e, httpx.TransportError)  # timeouts, connection errors

    def _gemini_embed_batch(self, texts: List[str]) -> List[List[float]]:
        from google.genai import types
        client = self._get_gemini_client()
        results = []
        for text in texts:
            try:
                resp = client.models.embed_content(
                    model="gemini-embedding-001",
                    contents=text,
                    config=types.EmbedContentConfig(output_dimensionality=GEMINI_EMBEDDING_DIMENSION),
                )
                results.append(resp.embeddings[0].values)
            except Exception as e:
                if not self._is_gemini_fallback_worthy(e):
                    raise
                logger.warning("Gemini unavailable (%s), falling back to OpenAI for this embedding", e)
                results.append(self._openai_embed_one(text, dimensions=GEMINI_EMBEDDING_DIMENSION))
        return results

    def _gemini_embed_one(self, text: str) -> List[float]:
        from google.genai import types
        client = self._get_gemini_client()
        try:
            resp = client.models.embed_content(
                model="gemini-embedding-001",
                contents=text,
                config=types.EmbedContentConfig(output_dimensionality=GEMINI_EMBEDDING_DIMENSION),
            )
            return resp.embeddings[0].values
        except Exception as e:
            if not self._is_gemini_fallback_worthy(e):
                raise
            logger.warning("Gemini unavailable (%s), falling back to OpenAI for this embedding", e)
            return self._openai_embed_one(text, dimensions=GEMINI_EMBEDDING_DIMENSION)

    # ------------------------------------------------------------------
    # OpenAI embeddings (text-embedding-3-small, 1536-dim; also used as a
    # same-dimension fallback when Gemini's quota is exhausted)
    # ------------------------------------------------------------------

    def _openai_embed_batch(
        self, texts: List[str], batch_size: int = 32, dimensions: Optional[int] = None
    ) -> List[List[float]]:
        client = self._get_openai_client()
        all_embeddings = []
        kwargs = {"dimensions": dimensions} if dimensions else {}
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            resp = client.embeddings.create(model=settings.EMBEDDING_MODEL, input=batch, **kwargs)
            all_embeddings.extend([item.embedding for item in resp.data])
        return all_embeddings

    def _openai_embed_one(self, text: str, dimensions: Optional[int] = None) -> List[float]:
        client = self._get_openai_client()
        kwargs = {"dimensions": dimensions} if dimensions else {}
        resp = client.embeddings.create(model=settings.EMBEDDING_MODEL, input=text, **kwargs)
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
            return GEMINI_EMBEDDING_DIMENSION
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
