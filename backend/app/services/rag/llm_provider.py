"""
LLM Provider Module

Provides unified interface for multiple LLM providers with automatic fallback.
Supports:
- Gemini (primary — free tier; also powers retrieval embeddings)
- OpenAI GPT (optional fallback — only active when OPENAI_API_KEY is set)
"""
import asyncio
import random
import time
from typing import Optional, List, Dict, AsyncGenerator
from abc import ABC, abstractmethod
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


# --- Transient-failure handling -------------------------------------------------

# Statuses a second attempt a fraction of a second later could plausibly clear:
# rate limiting and the various "try again" 5xx responses.
_RETRYABLE_STATUS = {408, 429, 500, 502, 503, 504}
_RETRY_BASE_DELAY = 0.2
_RETRY_MAX_DELAY = 4.0


class EmptyCompletionError(RuntimeError):
    """A provider returned no usable text - a safety block, a recitation stop,
    or a genuinely empty candidate. Treated as a provider failure so the
    fallback chain moves on instead of surfacing a blank answer."""


def _http_status(exc: Exception) -> Optional[int]:
    """Best-effort HTTP status for an SDK exception, or None for a
    transport-level failure that never received a response."""
    for attr in ("code", "status_code", "status"):
        val = getattr(exc, attr, None)
        if isinstance(val, int):
            return val
    resp = getattr(exc, "response", None)
    val = getattr(resp, "status_code", None)
    return val if isinstance(val, int) else None


def _is_retryable(exc: Exception) -> bool:
    """True for a rate-limit, a 5xx, or a network blip."""
    status = _http_status(exc)
    if status is not None:
        return status in _RETRYABLE_STATUS
    return isinstance(exc, (asyncio.TimeoutError, TimeoutError, ConnectionError, OSError))


async def _backoff(attempt: int) -> None:
    """Exponential backoff with full jitter; `attempt` is 0-based."""
    ceiling = min(_RETRY_MAX_DELAY, _RETRY_BASE_DELAY * (2 ** attempt))
    await asyncio.sleep(random.uniform(0, ceiling))


def _describe_empty(payload) -> str:
    """Human-readable reason a response or a stream carried no text."""
    try:
        feedback = getattr(payload, "prompt_feedback", None)
        block = getattr(feedback, "block_reason", None)
        if block:
            return f"prompt blocked ({getattr(block, 'name', block)})"
        candidates = getattr(payload, "candidates", None) or []
        if candidates:
            reason = getattr(candidates[0], "finish_reason", None)
            name = getattr(reason, "name", str(reason)) if reason is not None else None
            if name and name not in ("STOP", "None"):
                return f"no text (finish_reason={name})"
    except Exception:  # noqa: BLE001 - diagnostics only, must never raise
        pass
    return "empty response"


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
    """Google Gemini provider — free tier.

    Model id and display name are injectable so the same class can back both the
    primary model and a secondary fallback model, each carrying its own
    circuit-breaker state in LLMProvider. Every call retries transient failures
    (429 / 5xx / network) up to settings.GEMINI_MAX_ATTEMPTS times with jittered
    exponential backoff, and an empty or safety-blocked completion is raised as
    EmptyCompletionError so the fallback chain moves on rather than returning a
    blank answer.
    """

    def __init__(self, model: Optional[str] = None, name: str = "gemini"):
        self.model = model or settings.GEMINI_MODEL
        self._name = name
        self._client = None
        self._max_attempts = max(1, settings.GEMINI_MAX_ATTEMPTS)

    @property
    def name(self) -> str:
        return self._name

    @property
    def is_available(self) -> bool:
        return bool(settings.GEMINI_API_KEY and self.model)

    def _get_client(self):
        if self._client is None:
            from google import genai
            from google.genai import types
            # 60s (was 30s): broad/aggregation prompts have measured a ~32s
            # median and were tripping their own deadline.
            self._client = genai.Client(
                api_key=settings.GEMINI_API_KEY,
                http_options=types.HttpOptions(timeout=60_000),
            )
        return self._client

    def _config(self, system_prompt: str, temperature: float, max_tokens: int):
        from google.genai import types
        return types.GenerateContentConfig(
            system_instruction=system_prompt or None,
            temperature=temperature,
            max_output_tokens=max_tokens,
            # This is a straight RAG-answer task, not multi-step reasoning; at the
            # default thinking level, gemini-3.6-flash spends most of max_output_tokens
            # on hidden thinking tokens and truncates the actual answer before it starts.
            thinking_config=types.ThinkingConfig(thinking_level="low"),
        )

    async def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ) -> str:
        client = self._get_client()
        config = self._config(system_prompt, temperature, max_tokens)

        for attempt in range(self._max_attempts):
            try:
                response = await client.aio.models.generate_content(
                    model=self.model, contents=prompt, config=config,
                )
                try:
                    text = response.text
                except Exception:  # SDK raises when the only candidate was blocked
                    text = None
                if not text:
                    raise EmptyCompletionError(f"{self._name}: {_describe_empty(response)}")
                return text
            except EmptyCompletionError:
                raise
            except Exception as e:
                if attempt + 1 >= self._max_attempts or not _is_retryable(e):
                    raise
                logger.warning(
                    "Gemini (%s) attempt %d/%d failed: %s - retrying",
                    self.model, attempt + 1, self._max_attempts, e,
                )
                await _backoff(attempt)

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ) -> AsyncGenerator[str, None]:
        client = self._get_client()
        config = self._config(system_prompt, temperature, max_tokens)

        for attempt in range(self._max_attempts):
            emitted = False
            last = None
            try:
                async for chunk in await client.aio.models.generate_content_stream(
                    model=self.model, contents=prompt, config=config,
                ):
                    last = chunk
                    if chunk.text:
                        emitted = True
                        yield chunk.text
                if not emitted:
                    raise EmptyCompletionError(f"{self._name}: {_describe_empty(last)}")
                return
            except EmptyCompletionError:
                raise
            except Exception as e:
                # Retrying is only safe while nothing has been emitted - once a
                # token is out, a restart would splice two answers together.
                if emitted or attempt + 1 >= self._max_attempts or not _is_retryable(e):
                    raise
                logger.warning(
                    "Gemini (%s) stream attempt %d/%d failed: %s - retrying",
                    self.model, attempt + 1, self._max_attempts, e,
                )
                await _backoff(attempt)


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
            # timeout was 30s while broad/aggregation prompts measured a 32s
            # median - so those requests tripped their own deadline. Worse, the
            # SDK retries timeouts twice by default, turning one slow request
            # into three sequential ones before the caller ever sees an error.
            # Budget generously and retry once: a genuine outage still fails
            # over to the next provider quickly.
            self._client = openai.AsyncOpenAI(
                api_key=settings.OPENAI_API_KEY,
                timeout=60.0,
                max_retries=1,
            )
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
            model=settings.OPENAI_MODEL,
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
            model=settings.OPENAI_MODEL,
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
    1. Gemini, primary model (settings.GEMINI_MODEL)
    2. Gemini, fallback model (settings.GEMINI_FALLBACK_MODEL) — separate quota
       bucket and circuit breaker; skipped if unset or equal to the primary
    3. OpenAI (optional — skipped unless OPENAI_API_KEY is set)
    """

    # Once a provider fails this many times in a row it is skipped, but only
    # until CIRCUIT_BREAKER_COOLDOWN seconds have passed since its last failure
    # (half-open): a brief blip must not disable it for the whole process
    # lifetime, which is what happened before there was a cooldown. The
    # threshold is deliberately forgiving and the cooldown short - on a small
    # deployment the Gemini models are usually the only providers, so a long
    # lockout is close to a full outage. Per-call retries (GeminiProvider)
    # already absorb one-off transient errors before the breaker ever counts one.
    _circuit_breaker_threshold = 5
    _circuit_breaker_cooldown = 30.0

    def __init__(self):
        providers: List[LLMProviderBase] = [
            GeminiProvider(),  # primary (free tier)
        ]
        # A second Gemini model in its own quota bucket and behind its own
        # breaker, so a blip on the primary model does not take generation
        # fully offline (OpenAI is usually not configured). Disabled with an
        # empty GEMINI_FALLBACK_MODEL, or when it duplicates the primary.
        fallback_model = (settings.GEMINI_FALLBACK_MODEL or "").strip()
        if fallback_model and fallback_model != settings.GEMINI_MODEL:
            providers.append(GeminiProvider(model=fallback_model, name="gemini-fallback"))
        providers.append(OpenAIProvider())  # optional; skipped without OPENAI_API_KEY

        self.providers: List[LLMProviderBase] = providers
        self._failure_counts: Dict[str, int] = {p.name: 0 for p in self.providers}
        self._last_failure_at: Dict[str, float] = {p.name: 0.0 for p in self.providers}

    def _is_tripped(self, provider_name: str) -> bool:
        """True if the provider's breaker is open and still within its cooldown."""
        if self._failure_counts[provider_name] < self._circuit_breaker_threshold:
            return False
        if time.monotonic() - self._last_failure_at[provider_name] >= self._circuit_breaker_cooldown:
            # Cooldown elapsed — allow one trial request through.
            return False
        return True

    def _get_available_provider(self) -> Optional[LLMProviderBase]:
        """Get the first available provider whose breaker is not open."""
        for provider in self.providers:
            if provider.is_available and not self._is_tripped(provider.name):
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
        self._last_failure_at[provider_name] = time.monotonic()
    
    async def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """Generate a response with automatic fallback."""
        text, _ = await self.generate_with_provider(
            prompt, system_prompt, temperature, max_tokens
        )
        return text

    async def generate_with_provider(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> tuple[str, str]:
        """
        Generate a response with automatic fallback, reporting which provider
        served it.

        Returned rather than stashed on the instance: this is a singleton shared
        by every concurrent request, so an attribute recording "the last
        provider" would be read by the wrong request under load.

        Args:
            prompt: User prompt
            system_prompt: System instruction
            temperature: Model temperature
            max_tokens: Maximum tokens to generate

        Returns:
            (generated text, name of the provider that produced it)
        """
        temperature = temperature or settings.LLM_TEMPERATURE
        max_tokens = max_tokens or settings.LLM_MAX_TOKENS
        
        last_error = None
        
        for provider in self.providers:
            if not provider.is_available:
                continue
            
            if self._is_tripped(provider.name):
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
                return response, provider.name
            
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

        Raises:
            The last provider error, if every provider failed.
        """
        async for chunk, _ in self.stream_with_provider(
            prompt, system_prompt, temperature, max_tokens
        ):
            yield chunk

    async def stream_with_provider(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> AsyncGenerator[tuple[str, str], None]:
        """
        Stream a response with fallback, tagging each chunk with its provider.

        Fallback is only attempted before the first chunk is yielded. Once any
        text has reached the client it cannot be retracted, so a mid-stream
        failure is raised rather than silently restarted against another
        provider - which would splice two different answers together.

        The provider name rides on every chunk instead of being stashed on the
        instance: this is a singleton shared by all concurrent requests (see
        generate_with_provider).

        Yields:
            (text chunk, name of the provider producing it)

        Raises:
            The last provider error, if every provider failed before emitting.
        """
        temperature = temperature or settings.LLM_TEMPERATURE
        max_tokens = max_tokens or settings.LLM_MAX_TOKENS

        last_error = None

        for provider in self.providers:
            if not provider.is_available:
                continue

            if self._is_tripped(provider.name):
                logger.warning(f"Skipping {provider.name} due to repeated failures")
                continue

            emitted = False
            try:
                async for chunk in provider.generate_stream(
                    prompt,
                    system_prompt,
                    temperature,
                    max_tokens
                ):
                    emitted = True
                    yield chunk, provider.name
                self._record_success(provider.name)
                return

            except Exception as e:
                logger.error(f"Streaming error with {provider.name}: {e}")
                self._record_failure(provider.name)
                last_error = e
                if emitted:
                    # Partial answer already sent; the caller must surface the
                    # break rather than have another provider continue it.
                    raise

        if last_error:
            raise last_error
        raise RuntimeError("No LLM providers available")
    
    def get_current_provider(self) -> str:
        """Name of the provider that would be tried first, before any call."""
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
