"""Ollama local LLM provider implementation."""
from typing import List, Dict, Any
import ollama
from app.providers.base import BaseLLMProvider, Message, LLMResponse
from loguru import logger


class OllamaProvider(BaseLLMProvider):
    """Ollama local LLM provider."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.provider_name = "ollama"
        self.base_url = config.get("base_url", "http://localhost:11434")
        self.default_model = config.get("model", "llama3.1")

        # Initialize Ollama client
        self.client = ollama.AsyncClient(host=self.base_url)

    async def generate(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: int = 500,
        **kwargs,
    ) -> LLMResponse:
        """Generate response using Ollama."""
        model = kwargs.get("model", self.default_model)

        try:
            response = await self.client.chat(
                model=model,
                messages=[{"role": msg.role, "content": msg.content} for msg in messages],
                options={
                    "temperature": temperature,
                    "num_predict": max_tokens,
                },
            )

            return LLMResponse(
                content=response["message"]["content"],
                provider=self.provider_name,
                model=model,
                usage={
                    "prompt_tokens": response.get("prompt_eval_count", 0),
                    "completion_tokens": response.get("eval_count", 0),
                    "total_tokens": response.get("prompt_eval_count", 0) + response.get("eval_count", 0),
                },
                metadata={
                    "total_duration": response.get("total_duration"),
                    "load_duration": response.get("load_duration"),
                },
            )
        except Exception as e:
            logger.error(f"Ollama generation error: {e}")
            raise

    async def health_check(self) -> bool:
        """Check if Ollama is running and accessible."""
        try:
            # Try to list models as a health check
            await self.client.list()
            return True
        except Exception as e:
            logger.warning(f"Ollama health check failed: {e}")
            return False

    async def close(self):
        """Clean up Ollama client."""
        # Ollama client doesn't need explicit cleanup
        pass
