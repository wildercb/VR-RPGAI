"""Conversation and chat service with memory."""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models import Character, Conversation, Message, CharacterDocument
from app.providers.manager import llm_manager
from app.providers.base import Message as LLMMessage
from loguru import logger
import uuid


MAX_CONTEXT_MESSAGES = 20  # Keep last 20 messages in context


async def get_or_create_conversation(
    character_id: uuid.UUID, user_id: str, db: AsyncSession
) -> Conversation:
    """Get existing conversation or create a new one."""
    # Try to get existing active conversation
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
        # Create new conversation
        conversation = Conversation(
            id=uuid.uuid4(),
            character_id=character_id,
            user_id=user_id,
        )
        db.add(conversation)
        await db.commit()
        await db.refresh(conversation)

    return conversation


async def send_message(
    character_id: uuid.UUID,
    user_id: str,
    user_message: str,
    db: AsyncSession,
) -> tuple[str, Conversation]:
    """
    Send a message to a character and get a response.

    Args:
        character_id: ID of the character to talk to
        user_id: ID of the user sending the message
        user_message: The user's message content
        db: Database session

    Returns:
        Tuple of (assistant_response, conversation)
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

    # Load recent messages for context
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation.id)
        .order_by(Message.created_at.desc())
        .limit(MAX_CONTEXT_MESSAGES)
    )
    recent_messages = list(reversed(result.scalars().all()))

    # Build LLM context
    llm_messages = []

    # System prompt with character info
    system_content = character.system_prompt

    # Add document knowledge if available
    if character.documents:
        system_content += "\n\n**Reference Documents:**\n"
        for doc in character.documents:
            system_content += f"\n### {doc.filename}\n{doc.content}\n"

    llm_messages.append(LLMMessage(role="system", content=system_content))

    # Add conversation history
    for msg in recent_messages:
        llm_messages.append(LLMMessage(role=msg.role, content=msg.content))

    # Add current user message
    llm_messages.append(LLMMessage(role="user", content=user_message))

    # Generate response
    try:
        response = await llm_manager.generate(
            messages=llm_messages,
            provider=character.llm_provider,
            model=character.llm_model,
            temperature=character.temperature / 10.0,  # Convert from int storage
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

        logger.info(
            f"Conversation {conversation.id}: User message saved, assistant response generated"
        )

        return assistant_message, conversation

    except Exception as e:
        logger.error(f"Error generating response: {e}")
        raise


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
