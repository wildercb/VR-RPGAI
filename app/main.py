"""Main FastAPI application."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
from app.config import settings
from app.database import init_db, close_db
from app.providers.manager import llm_manager
from app.routers import characters, chat, documents, models
from loguru import logger
import os


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup
    logger.info("Starting RPGAI Character Agent System...")
    await init_db()
    await llm_manager.initialize()
    logger.info("System ready")

    yield

    # Shutdown
    logger.info("Shutting down...")
    await llm_manager.close()
    await close_db()
    logger.info("Shutdown complete")


app = FastAPI(
    title="RPGAI Character Agent System",
    description="Create and interact with AI characters for Unreal VR worlds",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS + ["*"],  # Allow all for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(characters.router, prefix="/api/characters", tags=["Characters"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(documents.router, prefix="/api/documents", tags=["Documents"])
app.include_router(models.router, prefix="/api/models", tags=["Models"])

# Mount static files
static_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.exists(static_path):
    app.mount("/static", StaticFiles(directory=static_path), name="static")

# Mount audio cache for TTS files
audio_cache_path = settings.AUDIO_CACHE_PATH
if os.path.exists(audio_cache_path):
    app.mount("/audio_cache", StaticFiles(directory=audio_cache_path), name="audio_cache")
else:
    # Create audio cache directory if it doesn't exist
    os.makedirs(audio_cache_path, exist_ok=True)
    app.mount("/audio_cache", StaticFiles(directory=audio_cache_path), name="audio_cache")


@app.get("/")
async def root():
    """Serve the web UI."""
    static_index = os.path.join(static_path, "index.html")
    if os.path.exists(static_index):
        return FileResponse(static_index)
    return {
        "name": "RPGAI Character Agent System",
        "version": "0.1.0",
        "docs": "/docs",
        "ui": "/static/index.html",
    }


@app.get("/demo-room.html")
async def demo_room():
    """Serve the interactive 3D demo room."""
    demo_path = os.path.join(static_path, "demo-room.html")
    if os.path.exists(demo_path):
        return FileResponse(demo_path)
    return {"detail": "Demo room not found"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    provider_health = await llm_manager.health_check()

    return {
        "status": "healthy",
        "providers": provider_health,
    }
