"""Chat and conversation endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from pydantic import UUID4

from app.database import get_db
from app.schemas import ChatRequest, ChatResponse, MessageResponse
from app.services import conversation_service_mem0 as conversation_service
from app.config import settings

router = APIRouter()


def get_user_id(x_user_id: str = Header(..., description="User ID")) -> str:
    """Extract user ID from header (simplified auth)."""
    return x_user_id


@router.post("/{character_id}", response_model=ChatResponse)
async def send_message(
    character_id: UUID4,
    data: ChatRequest,
    user_id: str = Depends(get_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Send a message to a character and get a response with semantic memory.

    The character will:
    - Retrieve relevant semantic memories about you
    - Use last 5 conversation messages for immediate context
    - Reference uploaded knowledge documents
    - Automatically learn new facts about you for future conversations
    """
    try:
        response_text, conversation = await conversation_service.send_message_with_memory(
            character_id=character_id,
            user_id=user_id,
            user_message=data.message,
            db=db,
        )

        return ChatResponse(
            conversation_id=conversation.id,
            message=response_text,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{conversation_id}/history", response_model=List[MessageResponse])
async def get_conversation_history(
    conversation_id: UUID4,
    user_id: str = Depends(get_user_id),
    db: AsyncSession = Depends(get_db),
    limit: int = 50,
):
    """Get conversation history."""
    try:
        messages = await conversation_service.get_conversation_history(
            conversation_id=conversation_id,
            user_id=user_id,
            db=db,
            limit=limit,
        )
        return messages
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{character_id}/memories")
async def get_character_memories(
    character_id: UUID4,
    user_id: str = Depends(get_user_id),
):
    """
    Get what the character remembers about you.

    Shows semantic memories extracted from past conversations.
    """
    try:
        memory_summary = await conversation_service.get_character_memory_summary(
            character_id=character_id,
            user_id=user_id
        )
        return memory_summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
