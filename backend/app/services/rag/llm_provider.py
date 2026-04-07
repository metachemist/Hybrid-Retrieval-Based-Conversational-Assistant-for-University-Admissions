"""
LLM Provider Module

Provides unified interface for multiple LLM providers with automatic fallback.
Supports:
- Anthropic Claude (primary)
- OpenAI GPT-3.5-turbo (fallback 1)
- Ollama local models (fallback 2)
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
    """Google Gemini provider — free tier via gemini-1.5-flash."""

    def __init__(self, model: str = "gemini-1.5-flash"):
        self.model = model
        self._configured = False

    @property
    def name(self) -> str:
        return "gemini"

    @property
    def is_available(self) -> bool:
        return settings.GEMINI_API_KEY is not None

    def _configure(self):
        if not self._configured:
            import google.generativeai as genai
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self._configured = True

    async def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ) -> str:
        self._configure()
        import google.generativeai as genai

        model = genai.GenerativeModel(
            model_name=self.model,
            system_instruction=system_prompt or None,
            generation_config=genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            ),
        )
        response = await model.generate_content_async(prompt)
        return response.text

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ) -> AsyncGenerator[str, None]:
        self._configure()
        import google.generativeai as genai

        model = genai.GenerativeModel(
            model_name=self.model,
            system_instruction=system_prompt or None,
            generation_config=genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            ),
        )
        response = await model.generate_content_async(prompt, stream=True)
        async for chunk in response:
            if chunk.text:
                yield chunk.text


class AnthropicProvider(LLMProviderBase):
    """Anthropic Claude provider."""
    
    def __init__(self):
        self._client = None
    
    @property
    def name(self) -> str:
        return "anthropic"
    
    @property
    def is_available(self) -> bool:
        return settings.ANTHROPIC_API_KEY is not None
    
    def _get_client(self):
        if self._client is None:
            import anthropic
            self._client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        return self._client
    
    async def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.3,
        max_tokens: int = 1024
    ) -> str:
        client = self._get_client()
        
        response = await client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return response.content[0].text
    
    async def generate_stream(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.3,
        max_tokens: int = 1024
    ) -> AsyncGenerator[str, None]:
        client = self._get_client()
        
        async with client.messages.stream(
            model="claude-haiku-4-5-20251001",
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt,
            messages=[{"role": "user", "content": prompt}]
        ) as stream:
            async for text in stream.text_stream:
                yield text


class OpenAIProvider(LLMProviderBase):
    """OpenAI GPT provider."""
    
    def __init__(self):
        self._client = None
    
    @property
    def name(self) -> str:
        return "openai"
    
    @property
    def is_available(self) -> bool:
        return settings.OPENAI_API_KEY is not None
    
    def _get_client(self):
        if self._client is None:
            import openai
            self._client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
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
            model="gpt-3.5-turbo",
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
            model="gpt-3.5-turbo",
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


class OllamaProvider(LLMProviderBase):
    """Ollama local model provider (zero-cost fallback)."""
    
    def __init__(self, model: str = "llama3:8b"):
        self.model = model
        self._client = None
    
    @property
    def name(self) -> str:
        return "ollama"
    
    @property
    def is_available(self) -> bool:
        # Ollama is always "available" but may not be running
        return True
    
    def _get_client(self):
        if self._client is None:
            import ollama
            self._client = ollama.AsyncClient(host=settings.OLLAMA_BASE_URL)
        return self._client
    
    async def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.3,
        max_tokens: int = 1024
    ) -> str:
        client = self._get_client()
        
        response = await client.generate(
            model=self.model,
            prompt=prompt,
            system=system_prompt,
            options={
                "temperature": temperature,
                "num_predict": max_tokens
            }
        )
        
        return response["response"]
    
    async def generate_stream(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.3,
        max_tokens: int = 1024
    ) -> AsyncGenerator[str, None]:
        client = self._get_client()
        
        response = await client.generate(
            model=self.model,
            prompt=prompt,
            system=system_prompt,
            stream=True,
            options={
                "temperature": temperature,
                "num_predict": max_tokens
            }
        )
        
        async for chunk in response:
            yield chunk["response"]


class LLMProvider:
    """
    Unified LLM provider with automatic fallback.
    
    Tries providers in order:
    1. Anthropic (primary)
    2. OpenAI (fallback 1)
    3. Ollama (fallback 2, local)
    """
    
    def __init__(self):
        self.providers: List[LLMProviderBase] = [
            GeminiProvider(),       # free tier — primary
            AnthropicProvider(),    # fallback 1
            OpenAIProvider(),       # fallback 2
            OllamaProvider(),       # fallback 3 (local)
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
