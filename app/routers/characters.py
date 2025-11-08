"""Character management endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from pydantic import UUID4

from app.database import get_db
from app.schemas import CharacterCreate, CharacterResponse
from app.services import character_service

router = APIRouter()


def get_user_id(x_user_id: str = Header(..., description="User ID")) -> str:
    """Extract user ID from header (simplified auth)."""
    return x_user_id


@router.post("/", response_model=CharacterResponse, status_code=201)
async def create_character(
    data: CharacterCreate,
    user_id: str = Depends(get_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new AI character from a simple prompt.

    Example prompt: "A wise wizard who teaches magic to beginners"

    The LLM will automatically generate:
    - Character name
    - Full personality and backstory
    - System prompt for interactions
    """
    try:
        character = await character_service.generate_character_from_prompt(
            user_id=user_id,
            prompt=data.prompt,
            db=db,
            llm_provider=data.llm_provider,
            llm_model=data.llm_model,
        )
        return character
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[CharacterResponse])
async def list_characters(
    user_id: str = Depends(get_user_id),
    db: AsyncSession = Depends(get_db),
):
    """List all characters for the current user."""
    characters = await character_service.list_characters(user_id, db)
    return characters


@router.get("/{character_id}", response_model=CharacterResponse)
async def get_character(
    character_id: UUID4,
    user_id: str = Depends(get_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific character by ID."""
    character = await character_service.get_character(character_id, user_id, db)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    return character


@router.delete("/{character_id}", status_code=204)
async def delete_character(
    character_id: UUID4,
    user_id: str = Depends(get_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Delete a character."""
    success = await character_service.delete_character(character_id, user_id, db)
    if not success:
        raise HTTPException(status_code=404, detail="Character not found")
    return None
