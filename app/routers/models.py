"""Model listing endpoints."""
from fastapi import APIRouter, HTTPException
from app.config import settings
import httpx
from loguru import logger

router = APIRouter()


@router.get("/ollama")
async def list_ollama_models():
    """
    List all available Ollama models.

    Returns list of models installed on the Ollama server.
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
            response.raise_for_status()
            data = response.json()

            models = [
                {
                    "name": model["name"],
                    "size": model.get("size", 0),
                    "modified_at": model.get("modified_at"),
                }
                for model in data.get("models", [])
            ]

            return {
                "provider": "ollama",
                "models": models,
                "base_url": settings.OLLAMA_BASE_URL
            }
    except httpx.HTTPError as e:
        logger.error(f"Failed to fetch Ollama models: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Ollama server not available at {settings.OLLAMA_BASE_URL}"
        )


@router.get("/openrouter")
async def list_openrouter_models():
    """
    List popular OpenRouter models.

    Returns a curated list of recommended models for character AI.
    """
    # Popular models for character AI (free and paid)
    models = [
        {
            "name": "meta-llama/llama-3.1-8b-instruct:free",
            "description": "Llama 3.1 8B - Free",
            "context_length": 8192,
            "pricing": "free"
        },
        {
            "name": "meta-llama/llama-3.1-70b-instruct",
            "description": "Llama 3.1 70B - High Quality",
            "context_length": 8192,
            "pricing": "paid"
        },
        {
            "name": "anthropic/claude-3.5-sonnet",
            "description": "Claude 3.5 Sonnet - Best Quality",
            "context_length": 200000,
            "pricing": "paid"
        },
        {
            "name": "openai/gpt-4-turbo",
            "description": "GPT-4 Turbo",
            "context_length": 128000,
            "pricing": "paid"
        },
        {
            "name": "google/gemini-pro-1.5",
            "description": "Gemini Pro 1.5",
            "context_length": 1000000,
            "pricing": "paid"
        },
        {
            "name": "mistralai/mistral-7b-instruct:free",
            "description": "Mistral 7B - Free",
            "context_length": 8192,
            "pricing": "free"
        },
    ]

    return {
        "provider": "openrouter",
        "models": models,
        "api_key_required": bool(settings.OPENROUTER_API_KEY),
        "note": "OpenRouter requires an API key. Free models have rate limits."
    }


@router.get("/providers")
async def list_providers():
    """
    List all available LLM providers and their status.
    """
    providers = []

    # Check Ollama
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
            providers.append({
                "name": "ollama",
                "status": "available",
                "type": "local",
                "url": settings.OLLAMA_BASE_URL
            })
    except:
        providers.append({
            "name": "ollama",
            "status": "unavailable",
            "type": "local",
            "url": settings.OLLAMA_BASE_URL
        })

    # Check OpenRouter
    if settings.OPENROUTER_API_KEY:
        providers.append({
            "name": "openrouter",
            "status": "configured",
            "type": "cloud",
            "url": "https://openrouter.ai"
        })
    else:
        providers.append({
            "name": "openrouter",
            "status": "not_configured",
            "type": "cloud",
            "url": "https://openrouter.ai",
            "note": "API key required in .env"
        })

    return {
        "providers": providers,
        "default": settings.DEFAULT_LLM_PROVIDER
    }
