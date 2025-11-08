"""OpenRouter LLM provider implementation."""
from typing import List, Dict, Any
import httpx
from app.providers.base import BaseLLMProvider, Message, LLMResponse
from loguru import logger


class OpenRouterProvider(BaseLLMProvider):
    """OpenRouter API provider - access to many models through one API."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.provider_name = "openrouter"
        self.api_key = config.get("api_key")
        self.base_url = "https://openrouter.ai/api/v1"
        self.default_model = config.get("model", "meta-llama/llama-3.1-8b-instruct:free")
        self.site_url = config.get("site_url", "")
        self.app_name = config.get("app_name", "RPGAI")

        if not self.api_key:
            raise ValueError("OpenRouter API key is required")

    async def generate(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: int = 500,
        **kwargs,
    ) -> LLMResponse:
        """Generate response using OpenRouter API."""
        model = kwargs.get("model", self.default_model)

        payload = {
            "model": model,
            "messages": [{"role": msg.role, "content": msg.content} for msg in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": self.site_url,
            "X-Title": self.app_name,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/chat/completions", json=payload, headers=headers
                )
                response.raise_for_status()
                data = response.json()

                return LLMResponse(
                    content=data["choices"][0]["message"]["content"],
                    provider=self.provider_name,
                    model=model,
                    usage=data.get("usage"),
                    metadata={
                        "finish_reason": data["choices"][0].get("finish_reason"),
                        "id": data.get("id"),
                    },
                )
            except httpx.HTTPError as e:
                logger.error(f"OpenRouter API error: {e}")
                raise

    async def health_check(self) -> bool:
        """Check OpenRouter API health."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                # Try a simple request to verify API key
                response = await client.get(
                    f"{self.base_url}/models", headers=headers
                )
                return response.status_code == 200
            except Exception as e:
                logger.warning(f"OpenRouter health check failed: {e}")
                return False
