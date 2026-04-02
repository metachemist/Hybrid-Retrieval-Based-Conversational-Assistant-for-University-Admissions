"""
RAG (Retrieval-Augmented Generation) Module

LLM integration with fallback providers and citation-grounded responses.
"""
from .llm_provider import LLMProvider, get_llm_provider
from .prompt import RAGPromptBuilder

__all__ = ["LLMProvider", "get_llm_provider", "RAGPromptBuilder"]
