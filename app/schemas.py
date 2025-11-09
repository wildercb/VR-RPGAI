"""Pydantic schemas for API requests and responses."""
from pydantic import BaseModel, UUID4
from typing import Optional
from datetime import datetime


# Character schemas
class CharacterCreate(BaseModel):
    """Request to create a new character from a prompt."""

    prompt: str
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None


class CharacterResponse(BaseModel):
    """Character response."""

    id: UUID4
    user_id: str
    name: str
    creation_prompt: str
    personality_summary: Optional[str]
    voice_id: str
    llm_provider: str
    llm_model: str
    created_at: datetime

    class Config:
        from_attributes = True


# Document schemas
class DocumentUpload(BaseModel):
    """Request to upload a document to a character."""

    filename: str
    content: str
    description: Optional[str] = None


class DocumentResponse(BaseModel):
    """Document response."""

    id: UUID4
    character_id: UUID4
    filename: str
    description: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# Chat schemas
class GameContext(BaseModel):
    """Game state context for enriched NPC responses."""

    location: Optional[str] = None
    weather: Optional[str] = None
    time_of_day: Optional[str] = None
    player_health: Optional[int] = None
    player_reputation: Optional[int] = None
    npc_health: Optional[int] = None
    npc_mood: Optional[str] = None
    recent_event: Optional[str] = None
    nearby_npcs: Optional[list[str]] = None
    custom_data: Optional[dict] = None


class ChatRequest(BaseModel):
    """Request to send a message to a character."""

    character_id: Optional[UUID4] = None  # Target character (required for /send endpoint)
    message: str
    context: Optional[GameContext] = None
    from_character_id: Optional[UUID4] = None  # For character-to-character chat


class ChatResponse(BaseModel):
    """Response from character."""

    conversation_id: UUID4
    message: str
    audio_file: Optional[str] = None
    audio_duration_ms: Optional[int] = None
    emotion: Optional[str] = None
    suggested_actions: Optional[list[dict]] = None


# Message history
class MessageResponse(BaseModel):
    """Individual message."""

    id: UUID4
    role: str
    content: str
    created_at: datetime
    audio_file: Optional[str] = None

    class Config:
        from_attributes = True
