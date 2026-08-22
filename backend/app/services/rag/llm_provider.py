"""
LLM Provider Module

Provides unified interface for multiple LLM providers with automatic fallback.
Supports:
- OpenAI GPT (primary — paid key, most reliable for production traffic)
- Gemini (fallback — free tier, stricter rate limits)
"""
import asyncio
from typing import Optional, List, Dict, AsyncGenerator
from abc import ABC, abstractmethod
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class LLMProviderBase(ABC):
    """Base class for LLM providers."""
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.3,
        max_tokens: int = 1024
    ) -> str:
        """Generate a response."""
        pass
    
    @abstractmethod
    async def generate_stream(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.3,
        max_tokens: int = 1024
    ) -> AsyncGenerator[str, None]:
        """Generate a streaming response."""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name."""
        pass
    
    @property
    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is configured and available."""
        pass


class GeminiProvider(LLMProviderBase):
    """Google Gemini provider — free tier via gemini-3.6-flash."""

    def __init__(self, model: str = "gemini-3.6-flash"):
        self.model = model
        self._client = None

    @property
    def name(self) -> str:
        return "gemini"

    @property
    def is_available(self) -> bool:
        return bool(settings.GEMINI_API_KEY)

    def _get_client(self):
        if self._client is None:
            from google import genai
            from google.genai import types
            self._client = genai.Client(
                api_key=settings.GEMINI_API_KEY,
                http_options=types.HttpOptions(timeout=30_000),
            )
        return self._client

    async def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ) -> str:
        from google.genai import types
        client = self._get_client()
        response = await client.aio.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt or None,
                temperature=temperature,
                max_output_tokens=max_tokens,
                # This is a straight RAG-answer task, not multi-step reasoning; at the
                # default thinking level, gemini-3.6-flash spends most of max_output_tokens
                # on hidden thinking tokens and truncates the actual answer before it starts.
                thinking_config=types.ThinkingConfig(thinking_level="low"),
            ),
        )
        return response.text

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ) -> AsyncGenerator[str, None]:
        from google.genai import types
        client = self._get_client()
        async for chunk in await client.aio.models.generate_content_stream(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt or None,
                temperature=temperature,
                max_output_tokens=max_tokens,
                # This is a straight RAG-answer task, not multi-step reasoning; at the
                # default thinking level, gemini-3.6-flash spends most of max_output_tokens
                # on hidden thinking tokens and truncates the actual answer before it starts.
                thinking_config=types.ThinkingConfig(thinking_level="low"),
            ),
        ):
            if chunk.text:
                yield chunk.text


class OpenAIProvider(LLMProviderBase):
    """OpenAI GPT provider."""
    
    def __init__(self):
        self._client = None
    
    @property
    def name(self) -> str:
        return "openai"
    
    @property
    def is_available(self) -> bool:
        return bool(settings.OPENAI_API_KEY)
    
    def _get_client(self):
        if self._client is None:
            import openai
            self._client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY, timeout=30.0)
        return self._client
    
    async def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.3,
        max_tokens: int = 1024
    ) -> str:
        client = self._get_client()
        
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return response.choices[0].message.content
    
    async def generate_stream(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.3,
        max_tokens: int = 1024
    ) -> AsyncGenerator[str, None]:
        client = self._get_client()
        
        stream = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True
        )
        
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


class LLMProvider:
    """
    Unified LLM provider with automatic fallback.

    Tries providers in order:
    1. OpenAI (primary — paid key, not subject to free-tier rate limits)
    2. Gemini (fallback, free tier)
    """

    def __init__(self):
        self.providers: List[LLMProviderBase] = [
            OpenAIProvider(),       # paid — primary
            GeminiProvider(),       # fallback (free tier)
        ]
        self._failure_counts: Dict[str, int] = {p.name: 0 for p in self.providers}
        self._circuit_breaker_threshold = 3  # failures before skipping provider
    
    def _get_available_provider(self) -> Optional[LLMProviderBase]:
        """Get the first available provider that hasn't exceeded failure threshold."""
        for provider in self.providers:
            if provider.is_available and self._failure_counts[provider.name] < self._circuit_breaker_threshold:
                return provider
        return None
    
    def _record_success(self, provider_name: str):
        """Record successful request for a provider."""
        self._failure_counts[provider_name] = 0
    
    def _record_failure(self, provider_name: str):
        """Record failed request for a provider."""
        self._failure_counts[provider_name] = min(
            self._failure_counts[provider_name] + 1,
            self._circuit_breaker_threshold + 1
        )
    
    async def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Generate a response with automatic fallback.
        
        Args:
            prompt: User prompt
            system_prompt: System instruction
            temperature: Model temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated response text
        """
        temperature = temperature or settings.LLM_TEMPERATURE
        max_tokens = max_tokens or settings.LLM_MAX_TOKENS
        
        last_error = None
        
        for provider in self.providers:
            if not provider.is_available:
                continue
            
            if self._failure_counts[provider.name] >= self._circuit_breaker_threshold:
                logger.warning(f"Skipping {provider.name} due to repeated failures")
                continue
            
            try:
                response = await provider.generate(
                    prompt,
                    system_prompt,
                    temperature,
                    max_tokens
                )
                self._record_success(provider.name)
                logger.info(f"Successfully generated response using {provider.name}")
                return response
            
            except Exception as e:
                logger.error(f"Error with {provider.name}: {e}")
                self._record_failure(provider.name)
                last_error = e
        
        # All providers failed
        if last_error:
            raise last_error
        raise RuntimeError("No LLM providers available")
    
    async def generate_stream(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> AsyncGenerator[str, None]:
        """
        Generate a streaming response with automatic fallback.
        
        Yields:
            Generated text chunks
        """
        temperature = temperature or settings.LLM_TEMPERATURE
        max_tokens = max_tokens or settings.LLM_MAX_TOKENS
        
        provider = self._get_available_provider()
        if not provider:
            raise RuntimeError("No LLM providers available")
        
        try:
            async for chunk in provider.generate_stream(
                prompt,
                system_prompt,
                temperature,
                max_tokens
            ):
                yield chunk
            self._record_success(provider.name)
        except Exception as e:
            logger.error(f"Streaming error with {provider.name}: {e}")
            self._record_failure(provider.name)
            # For streaming, we can't easily fallback mid-stream
            # Return error message as final chunk
            yield f"\n\n[Error: {str(e)}]"
    
    def get_current_provider(self) -> str:
        """Get the name of the primary available provider."""
        provider = self._get_available_provider()
        return provider.name if provider else "none"


# Singleton instance
_llm_provider = None


def get_llm_provider() -> LLMProvider:
    """Get or create the LLM provider singleton."""
    global _llm_provider
    if _llm_provider is None:
        _llm_provider = LLMProvider()
    return _llm_provider
