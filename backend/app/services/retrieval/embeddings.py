"""
Embedding Model Module

Provides sentence embeddings for semantic search.
Uses OpenAI embeddings for simplicity and reliability.
"""
from typing import List, Optional
import numpy as np
from openai import OpenAI

import sys
sys.path.insert(0, '/home/metachemist/Code/FYP/backend')
from app.core.config import settings


class EmbeddingModel:
    """
    Wrapper for generating embeddings using OpenAI API.
    
    Uses text-embedding-3-small which supports:
    - English
    - Roman Urdu
    - Code-mixed text
    """
    
    def __init__(self, model_name: Optional[str] = None):
        """
        Initialize the embedding model.
        
        Args:
            model_name: Name of the OpenAI embedding model
        """
        self.model_name = model_name or settings.EMBEDDING_MODEL
        self._client = None
        self._dimension = settings.EMBEDDING_DIMENSION
    
    def _get_client(self) -> OpenAI:
        """Get or create OpenAI client."""
        if self._client is None:
            from ..core.config import settings
            self._client = OpenAI(api_key=settings.OPENAI_API_KEY or "")
        return self._client
    
    def encode(
        self,
        texts: List[str],
        batch_size: int = 32,
        show_progress: bool = False
    ) -> np.ndarray:
        """
        Generate embeddings for texts.
        
        Args:
            texts: List of texts to embed
            batch_size: Batch size for encoding
            show_progress: Show progress bar
            
        Returns:
            Numpy array of embeddings
        """
        client = self._get_client()
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            response = client.embeddings.create(
                model=self.model_name,
                input=batch
            )
            batch_embeddings = [item.embedding for item in response.data]
            all_embeddings.extend(batch_embeddings)
            
            if show_progress:
                print(f"Processed {min(i + batch_size, len(texts))}/{len(texts)} texts")
        
        return np.array(all_embeddings)
    
    def encode_query(self, text: str) -> np.ndarray:
        """
        Generate embedding for a search query.
        
        Args:
            text: Query text
            
        Returns:
            Query embedding vector
        """
        client = self._get_client()
        response = client.embeddings.create(
            model=self.model_name,
            input=text
        )
        return np.array(response.data[0].embedding)
    
    def get_dimension(self) -> int:
        """Get the embedding dimension."""
        return self._dimension


# Singleton instance
_embedding_model = None


def get_embedding_model() -> EmbeddingModel:
    """Get or create the embedding model singleton."""
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = EmbeddingModel()
    return _embedding_model


def initialize_model():
    """Pre-load the embedding model (call at startup)."""
    model = get_embedding_model()
    # No pre-loading needed for API-based embeddings
