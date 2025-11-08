"""LLM Provider Manager - handles multiple providers."""
from typing import Dict, Any, Optional
from app.providers.base import BaseLLMProvider, Message, LLMResponse
from app.providers.ollama_provider import OllamaProvider
from app.providers.openrouter_provider import OpenRouterProvider
from app.config import settings
from loguru import logger


class LLMProviderManager:
    """Manages multiple LLM providers and routes requests."""

    def __init__(self):
        self.providers: Dict[str, BaseLLMProvider] = {}
        self._initialized = False

    async def initialize(self):
        """Initialize all configured providers."""
        if self._initialized:
            return

        # Initialize Ollama if configured
        if settings.OLLAMA_BASE_URL:
            try:
                self.providers["ollama"] = OllamaProvider(
                    {
                        "base_url": settings.OLLAMA_BASE_URL,
                        "model": settings.OLLAMA_MODEL,
                    }
                )
                logger.info("Ollama provider initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Ollama: {e}")

        # Initialize OpenRouter if API key is set
        if settings.OPENROUTER_API_KEY:
            try:
                self.providers["openrouter"] = OpenRouterProvider(
                    {
                        "api_key": settings.OPENROUTER_API_KEY,
                        "model": settings.OPENROUTER_MODEL,
                        "site_url": settings.OPENROUTER_SITE_URL,
                        "app_name": "RPGAI",
                    }
                )
                logger.info("OpenRouter provider initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenRouter: {e}")

        self._initialized = True
        logger.info(f"Initialized {len(self.providers)} LLM providers: {list(self.providers.keys())}")

    async def generate(
        self,
        messages: list[Message],
        provider: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 500,
    ) -> LLMResponse:
        """
        Generate a response using specified or default provider.

        Args:
            messages: List of conversation messages
            provider: Provider name ("ollama", "openrouter") or None for default
            model: Model name or None for provider default
            temperature: Sampling temperature
            max_tokens: Max tokens to generate

        Returns:
            LLMResponse from the selected provider
        """
        if not self._initialized:
            await self.initialize()

        # Use default provider if none specified
        if not provider:
            provider = settings.DEFAULT_LLM_PROVIDER

        # Get the provider
        if provider not in self.providers:
            available = list(self.providers.keys())
            if not available:
                raise ValueError("No LLM providers are configured")
            # Fallback to first available provider
            provider = available[0]
            logger.warning(f"Requested provider not available, using {provider}")

        llm = self.providers[provider]

        # Generate response
        kwargs = {}
        if model:
            kwargs["model"] = model

        return await llm.generate(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )

    async def health_check(self) -> Dict[str, bool]:
        """Check health of all providers."""
        if not self._initialized:
            await self.initialize()

        results = {}
        for name, provider in self.providers.items():
            results[name] = await provider.health_check()

        return results

    async def close(self):
        """Clean up all providers."""
        for provider in self.providers.values():
            await provider.close()
        self.providers.clear()
        self._initialized = False


# Global provider manager instance
llm_manager = LLMProviderManager()
