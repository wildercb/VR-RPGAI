"""Simplified database models for AI characters."""
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid
from app.database import Base


def utc_now():
    """Get current UTC time in timezone-naive format."""
    return datetime.utcnow()


class Character(Base):
    """AI Character - created from user prompt, LLM generates the rest."""

    __tablename__ = "characters"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(255), nullable=False, index=True)  # Owner of this character
    name = Column(String(255), nullable=False)

    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    # User's original prompt
    creation_prompt = Column(Text, nullable=False)  # e.g., "A wise wizard who teaches magic"

    # LLM-generated character profile
    system_prompt = Column(Text, nullable=False)  # Full system prompt for LLM
    personality_summary = Column(Text, nullable=True)  # Brief description for display

    # Voice settings
    voice_id = Column(String(100), default="en_US-lessac-medium")

    # LLM settings
    llm_provider = Column(String(50), default="ollama")  # "ollama" or "openrouter"
    llm_model = Column(String(100), default="llama3.1")
    temperature = Column(Integer, default=7)  # Store as int (0-20), divide by 10

    is_active = Column(Boolean, default=True)

    # Relationships
    documents = relationship("CharacterDocument", back_populates="character", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="character", cascade="all, delete-orphan")
    semantic_memories = relationship("CharacterMemory", back_populates="character", cascade="all, delete-orphan")


class CharacterDocument(Base):
    """Documents uploaded to give character specialized knowledge."""

    __tablename__ = "character_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    character_id = Column(UUID(as_uuid=True), ForeignKey("characters.id", ondelete="CASCADE"), nullable=False)

    created_at = Column(DateTime, default=utc_now)

    filename = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)  # Full text content of the document
    description = Column(String(500), nullable=True)  # Optional: what this doc is about

    # Relationships
    character = relationship("Character", back_populates="documents")


class Conversation(Base):
    """Conversation between a user and a character."""

    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    character_id = Column(UUID(as_uuid=True), ForeignKey("characters.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String(255), nullable=False, index=True)

    created_at = Column(DateTime, default=utc_now)
    last_message_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    # Relationships
    character = relationship("Character", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at")
    summary = relationship("ConversationSummary", back_populates="conversation", uselist=False, cascade="all, delete-orphan")


class Message(Base):
    """Individual message in a conversation."""

    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)

    created_at = Column(DateTime, default=utc_now)

    role = Column(String(20), nullable=False)  # "user" or "assistant"
    content = Column(Text, nullable=False)

    # For assistant messages with voice
    audio_file = Column(String(500), nullable=True)  # Path to cached audio file
    audio_duration_ms = Column(Integer, nullable=True)

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
"""Enhanced memory models for semantic retrieval and context building."""
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer, Boolean, Float, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from datetime import datetime, timezone
import uuid
from app.database import Base


def utc_now():
    """Get current UTC time in timezone-naive format."""
    return datetime.utcnow()


class CharacterMemory(Base):
    """
    Semantic memory system for characters.

    Stores:
    - Facts learned about the user
    - Character's experiences and reflections
    - Important events from conversations

    Uses embeddings for semantic retrieval.
    """
    __tablename__ = "character_memories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    character_id = Column(UUID(as_uuid=True), ForeignKey("characters.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(255), nullable=False, index=True)  # Which user this memory is about

    created_at = Column(DateTime, default=utc_now, nullable=False)
    last_accessed = Column(DateTime, default=utc_now)
    access_count = Column(Integer, default=0)

    # Memory content
    memory_type = Column(String(50), nullable=False, index=True)  # "user_fact", "character_reflection", "event", "preference"
    content = Column(Text, nullable=False)
    importance = Column(Float, default=0.5)  # 0.0 to 1.0, used for retrieval ranking

    # Semantic search
    embedding = Column(Vector(384))  # Sentence transformer embeddings (384 dimensions)

    # Metadata
    source_conversation_id = Column(UUID(as_uuid=True), nullable=True)  # Where this memory came from
    tags = Column(Text, nullable=True)  # JSON array of tags

    # Relationships
    character = relationship("Character", back_populates="semantic_memories")

    __table_args__ = (
        Index('idx_character_user_memories', 'character_id', 'user_id'),
        Index('idx_memory_embedding', 'embedding', postgresql_using='ivfflat', postgresql_ops={'embedding': 'vector_cosine_ops'}),
    )


class UserProfile(Base):
    """
    User profile that evolves across all character interactions.

    Stores what different characters learn about the same user.
    """
    __tablename__ = "user_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(255), nullable=False, unique=True, index=True)

    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    # Aggregated user information
    user_summary = Column(Text, nullable=True)  # LLM-generated summary of user
    preferences = Column(Text, nullable=True)  # JSON object of learned preferences
    interaction_count = Column(Integer, default=0)

    # Relationships
    memories = relationship("UserMemory", back_populates="profile", cascade="all, delete-orphan")


class UserMemory(Base):
    """
    Cross-character memory about a user.

    Facts that multiple characters can access and learn from.
    """
    __tablename__ = "user_memories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(255), ForeignKey("user_profiles.user_id", ondelete="CASCADE"), nullable=False, index=True)

    created_at = Column(DateTime, default=utc_now)
    last_accessed = Column(DateTime, default=utc_now)
    access_count = Column(Integer, default=0)

    # Memory content
    memory_type = Column(String(50), nullable=False)  # "fact", "preference", "goal", "background"
    content = Column(Text, nullable=False)
    confidence = Column(Float, default=0.5)  # How confident we are in this memory

    # Semantic search
    embedding = Column(Vector(384))

    # Source tracking
    learned_from_character_id = Column(UUID(as_uuid=True), nullable=True)  # Which character discovered this
    source_conversation_id = Column(UUID(as_uuid=True), nullable=True)

    # Relationships
    profile = relationship("UserProfile", back_populates="memories")

    __table_args__ = (
        Index('idx_user_memory_embedding', 'embedding', postgresql_using='ivfflat', postgresql_ops={'embedding': 'vector_cosine_ops'}),
    )


class ConversationSummary(Base):
    """
    LLM-generated summaries of conversations for long-term context.

    As conversations grow, we summarize them to reduce token usage.
    """
    __tablename__ = "conversation_summaries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, unique=True)

    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    # Summary content
    summary = Column(Text, nullable=False)  # LLM-generated summary
    message_count = Column(Integer, default=0)  # How many messages this summary covers
    last_summarized_message_id = Column(UUID(as_uuid=True), nullable=True)

    # Key points extracted
    key_facts = Column(Text, nullable=True)  # JSON array of important facts
    topics_discussed = Column(Text, nullable=True)  # JSON array of topics

    # Relationships
    conversation = relationship("Conversation", back_populates="summary")


class MemoryExtractionJob(Base):
    """
    Track background jobs for extracting memories from conversations.

    Memories are extracted asynchronously after conversations.
    """
    __tablename__ = "memory_extraction_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)

    created_at = Column(DateTime, default=utc_now)
    completed_at = Column(DateTime, nullable=True)

    status = Column(String(50), default="pending")  # "pending", "processing", "completed", "failed"
    last_processed_message_id = Column(UUID(as_uuid=True), nullable=True)

    error_message = Column(Text, nullable=True)
    memories_extracted = Column(Integer, default=0)
