"""Base LLM provider interface."""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
from pydantic import BaseModel


class Message(BaseModel):
    """Chat message format."""

    role: str  # "system", "user", "assistant"
    content: str


class LLMResponse(BaseModel):
    """Standardized LLM response."""

    content: str
    provider: str
    model: str
    usage: Optional[Dict[str, int]] = None
    metadata: Dict[str, Any] = {}


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize provider with configuration."""
        self.config = config
        self.provider_name = "base"

    @abstractmethod
    async def generate(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: int = 500,
        **kwargs,
    ) -> LLMResponse:
        """
        Generate a response from the LLM.

        Args:
            messages: List of conversation messages
            temperature: Sampling temperature (0.0 to 2.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Provider-specific parameters

        Returns:
            LLMResponse with generated content
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the provider is available and healthy."""
        pass

    async def close(self):
        """Clean up resources (override if needed)."""
        pass
