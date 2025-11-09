"""Enhanced conversation service with Mem0 semantic memory."""
from typing import Optional, List, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models import Character, Conversation, Message, CharacterDocument
from app.providers.manager import llm_manager
from app.providers.base import Message as LLMMessage
from app.services.memory_service import memory_service
from app.services.tts_service import tts_service
from app.config import settings
from loguru import logger
import uuid


RECENT_MESSAGES_LIMIT = 5  # Only keep last 5 messages for immediate context


async def get_or_create_conversation(
    character_id: uuid.UUID, user_id: str, db: AsyncSession
) -> Conversation:
    """Get existing conversation or create a new one."""
    result = await db.execute(
        select(Conversation)
        .options(selectinload(Conversation.messages))
        .where(
            Conversation.character_id == character_id,
            Conversation.user_id == user_id,
        )
        .order_by(Conversation.last_message_at.desc())
        .limit(1)
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        conversation = Conversation(
            id=uuid.uuid4(),
            character_id=character_id,
            user_id=user_id,
        )
        db.add(conversation)
        await db.commit()
        await db.refresh(conversation)

    return conversation


async def send_message_with_memory(
    character_id: uuid.UUID,
    user_id: str,
    user_message: str,
    db: AsyncSession,
    game_context: Optional[Dict] = None,
    from_character_id: Optional[uuid.UUID] = None,
) -> tuple[str, Conversation, Optional[str]]:
    """
    Send a message with Mem0-powered semantic memory retrieval and TTS audio generation.

    Flow:
    1. Retrieve relevant memories about user (semantic search)
    2. Get recent conversation messages (last 5)
    3. Build enriched context with memories + documents + game state
    4. Generate response
    5. Generate TTS audio for response
    6. Save message and extract new memories asynchronously

    Args:
        character_id: ID of the character
        user_id: ID of the user
        user_message: User's message
        db: Database session
        game_context: Optional game state context (location, weather, events, etc.)
        from_character_id: Optional ID of character sending the message (for NPC-to-NPC)

    Returns:
        Tuple of (assistant_response, conversation, audio_file_path)
    """
    # Get the character with documents
    result = await db.execute(
        select(Character)
        .options(selectinload(Character.documents))
        .where(Character.id == character_id, Character.is_active == True)
    )
    character = result.scalar_one_or_none()

    if not character:
        raise ValueError(f"Character {character_id} not found")

    # Get or create conversation
    conversation = await get_or_create_conversation(character_id, user_id, db)

    # Step 1: Retrieve relevant memories using Mem0 (semantic search)
    character_memories = []
    user_global_memories = []

    if settings.MEM0_ENABLE_MEMORY:
        try:
            # Get character-specific memories about this user
            character_memories = memory_service.get_character_memories(
                character_id=str(character_id),
                user_id=user_id,
                query=user_message,  # Semantic search based on current message
                limit=5
            )

            # Get user-global memories (facts that span across characters)
            user_global_memories = memory_service.get_user_global_memories(
                user_id=user_id,
                query=user_message,
                limit=3
            )

            logger.info(f"Retrieved {len(character_memories)} character memories, {len(user_global_memories)} global memories")
        except Exception as e:
            logger.warning(f"Memory retrieval failed, continuing without memory: {e}")

    # Step 2: Get recent messages (reduced from 20 to 5 since we have memories)
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation.id)
        .order_by(Message.created_at.desc())
        .limit(RECENT_MESSAGES_LIMIT)
    )
    recent_messages = list(reversed(result.scalars().all()))

    # Step 3: Build enriched LLM context
    llm_messages = []

    # System prompt with character info
    system_content = character.system_prompt

    # Add uploaded documents (reference knowledge)
    if character.documents:
        system_content += "\n\n**Reference Documents:**\n"
        for doc in character.documents:
            system_content += f"\n### {doc.filename}\n{doc.content[:2000]}\n"  # Limit doc size

    # Add semantic memories to system prompt
    if character_memories:
        system_content += "\n\n**What you remember about this user:**\n"
        for mem in character_memories:
            memory_text = mem.get('memory', mem.get('data', ''))
            system_content += f"- {memory_text}\n"

    if user_global_memories:
        system_content += "\n\n**General facts about this user:**\n"
        for mem in user_global_memories:
            memory_text = mem.get('memory', mem.get('data', ''))
            system_content += f"- {memory_text}\n"

    # Add game context if provided
    if game_context:
        system_content += "\n\n**Current Game State:**\n"
        if game_context.get('location'):
            system_content += f"Location: {game_context['location']}\n"
        if game_context.get('weather'):
            system_content += f"Weather: {game_context['weather']}\n"
        if game_context.get('time_of_day'):
            system_content += f"Time: {game_context['time_of_day']}\n"
        if game_context.get('npc_health') is not None:
            system_content += f"Your health: {game_context['npc_health']}%\n"
        if game_context.get('player_health') is not None:
            system_content += f"Player health: {game_context['player_health']}%\n"
        if game_context.get('player_reputation') is not None:
            system_content += f"Player reputation: {game_context['player_reputation']}\n"
        if game_context.get('npc_mood'):
            system_content += f"Your mood: {game_context['npc_mood']}\n"
        if game_context.get('recent_event'):
            system_content += f"Recent event: {game_context['recent_event']}\n"
        if game_context.get('nearby_npcs'):
            system_content += f"Nearby NPCs: {', '.join(game_context['nearby_npcs'])}\n"
        if game_context.get('custom_data'):
            for key, value in game_context['custom_data'].items():
                system_content += f"{key}: {value}\n"

    # Handle character-to-character communication
    if from_character_id:
        # Get the sending character's name
        result = await db.execute(
            select(Character).where(Character.id == from_character_id)
        )
        from_character = result.scalar_one_or_none()
        if from_character:
            system_content += f"\n\n**Note:** This message is from {from_character.name}, another character in the world. Respond as if speaking to them directly.\n"
            user_id = f"character_{from_character_id}"  # Use character ID as "user" for multi-agent

    llm_messages.append(LLMMessage(role="system", content=system_content))

    # Add recent conversation history (only last 5 messages)
    for msg in recent_messages:
        llm_messages.append(LLMMessage(role=msg.role, content=msg.content))

    # Add current user message
    llm_messages.append(LLMMessage(role="user", content=user_message))

    # Step 4: Generate response
    try:
        response = await llm_manager.generate(
            messages=llm_messages,
            provider=character.llm_provider,
            model=character.llm_model,
            temperature=character.temperature / 10.0,
            max_tokens=500,
        )

        assistant_message = response.content

        # Save user message
        user_msg = Message(
            id=uuid.uuid4(),
            conversation_id=conversation.id,
            role="user",
            content=user_message,
        )
        db.add(user_msg)

        # Save assistant message
        assistant_msg = Message(
            id=uuid.uuid4(),
            conversation_id=conversation.id,
            role="assistant",
            content=assistant_message,
        )
        db.add(assistant_msg)

        # Update conversation timestamp
        from app.models import utc_now
        conversation.last_message_at = utc_now()

        await db.commit()

        # Step 5: Generate TTS audio if enabled
        audio_file = None
        audio_duration_ms = None
        if settings.TTS_ENABLED:
            try:
                # Use character's voice_id if available, otherwise use default
                voice = character.voice_id if hasattr(character, 'voice_id') and character.voice_id else None
                audio_path = await tts_service.synthesize(
                    text=assistant_message,
                    voice=voice,
                    use_cache=True
                )
                if audio_path:
                    # Store relative path for API response
                    audio_file = audio_path.replace('/app/', '')
                    logger.info(f"Generated TTS audio: {audio_file}")
            except Exception as e:
                logger.warning(f"TTS generation failed (non-critical): {e}")

        # Step 6: Extract and save new memories asynchronously (non-blocking)
        if settings.MEM0_ENABLE_MEMORY:
            try:
                _extract_memories_from_exchange(
                    character_id=str(character_id),
                    user_id=user_id,
                    user_message=user_message,
                    assistant_message=assistant_message,
                    conversation_id=str(conversation.id)
                )
            except Exception as e:
                logger.warning(f"Memory extraction failed (non-critical): {e}")

        logger.info(f"Conversation {conversation.id}: Response generated with {len(character_memories)} memories")

        return assistant_message, conversation, audio_file

    except Exception as e:
        logger.error(f"Error generating response: {e}")
        raise


def _extract_memories_from_exchange(
    character_id: str,
    user_id: str,
    user_message: str,
    assistant_message: str,
    conversation_id: str
):
    """
    Extract memories from a user-assistant exchange.

    Mem0 will automatically extract:
    - Facts about the user
    - User preferences
    - Important events
    - Character reflections

    This runs synchronously but is called in a non-blocking way.
    For production, use a background task queue (Celery, etc.)
    """
    messages = [
        {"role": "user", "content": user_message},
        {"role": "assistant", "content": assistant_message},
    ]

    metadata = {
        "conversation_id": conversation_id,
        "timestamp": str(uuid.uuid4())  # Use timestamp in production
    }

    memory_service.add_character_memory(
        character_id=character_id,
        user_id=user_id,
        messages=messages,
        metadata=metadata
    )


async def get_conversation_history(
    conversation_id: uuid.UUID, user_id: str, db: AsyncSession, limit: int = 50
) -> list[Message]:
    """Get conversation history."""
    result = await db.execute(
        select(Message)
        .join(Conversation)
        .where(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id,
        )
        .order_by(Message.created_at.desc())
        .limit(limit)
    )
    return list(reversed(result.scalars().all()))


async def get_character_memory_summary(
    character_id: uuid.UUID,
    user_id: str
) -> Dict:
    """
    Get a summary of what the character remembers about the user.

    Returns:
        Dictionary with memory summary and statistics
    """
    if not settings.MEM0_ENABLE_MEMORY:
        return {"enabled": False, "memories": []}

    try:
        memories = memory_service.get_character_memories(
            character_id=str(character_id),
            user_id=user_id,
            limit=20
        )

        return {
            "enabled": True,
            "total_memories": len(memories),
            "memories": [
                {
                    "id": mem.get('id'),
                    "content": mem.get('memory', mem.get('data', '')),
                    "created_at": mem.get('created_at'),
                }
                for mem in memories
            ]
        }
    except Exception as e:
        logger.error(f"Error getting memory summary: {e}")
        return {"enabled": True, "error": str(e), "memories": []}
