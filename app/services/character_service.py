"""Character creation and management service."""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import Character
from app.providers.manager import llm_manager
from app.providers.base import Message
from loguru import logger
import uuid


CHARACTER_GENERATION_PROMPT = """You are a character profile generator for an AI-driven VR RPG system.

Given a user's character concept, generate a comprehensive character profile in the following format:

**Character Name:** [Generate an appropriate name]

**Personality Summary:** [2-3 sentences describing the character's core personality, role, and purpose]

**System Prompt:**
[Generate a detailed system prompt that this character will use when interacting with users. This should include:
- Who they are and their background
- Their personality traits and how they speak
- Their knowledge domain and expertise
- How they should respond to users
- Their goals in interactions

The system prompt should be written in second person ("You are...") and be comprehensive enough that an LLM can roleplay this character convincingly.]

---

User's Character Concept: {concept}

Generate the character profile now:"""


async def generate_character_from_prompt(
    user_id: str,
    prompt: str,
    db: AsyncSession,
    llm_provider: Optional[str] = None,
    llm_model: Optional[str] = None,
) -> Character:
    """
    Generate a complete character profile from a user prompt using LLM.

    Args:
        user_id: ID of the user creating the character
        prompt: User's character concept (e.g., "A wise wizard who teaches magic")
        db: Database session
        llm_provider: Optional LLM provider to use
        llm_model: Optional model to use

    Returns:
        Created Character instance
    """
    logger.info(f"Generating character for user {user_id} from prompt: {prompt}")

    # Generate character profile using LLM
    generation_prompt = CHARACTER_GENERATION_PROMPT.format(concept=prompt)

    try:
        response = await llm_manager.generate(
            messages=[Message(role="user", content=generation_prompt)],
            provider=llm_provider,
            model=llm_model,
            temperature=0.8,
            max_tokens=1000,
        )

        generated_content = response.content

        # Parse the generated content
        name = _extract_field(generated_content, "Character Name")
        personality_summary = _extract_field(generated_content, "Personality Summary")
        system_prompt = _extract_field(generated_content, "System Prompt")

        # Fallback if parsing fails
        if not name:
            name = "Generated Character"
        if not personality_summary:
            personality_summary = prompt
        if not system_prompt:
            system_prompt = f"You are a character in a VR world. {prompt}"

        logger.info(f"Generated character '{name}' successfully")

        # Create character in database
        character = Character(
            id=uuid.uuid4(),
            user_id=user_id,
            name=name,
            creation_prompt=prompt,
            system_prompt=system_prompt,
            personality_summary=personality_summary,
            llm_provider=llm_provider or "ollama",
            llm_model=llm_model or "llama3.1",
        )

        db.add(character)
        await db.commit()
        await db.refresh(character)

        return character

    except Exception as e:
        logger.error(f"Error generating character: {e}")
        raise


def _extract_field(text: str, field_name: str) -> Optional[str]:
    """Extract a field from the generated text."""
    marker = f"**{field_name}:**"
    if marker not in text:
        return None

    start = text.find(marker) + len(marker)
    # Find next ** or end of text
    end = text.find("**", start)
    if end == -1:
        end = len(text)

    content = text[start:end].strip()
    return content if content else None


async def get_character(
    character_id: uuid.UUID, user_id: str, db: AsyncSession
) -> Optional[Character]:
    """Get a character by ID, ensuring it belongs to the user."""
    result = await db.execute(
        select(Character).where(
            Character.id == character_id,
            Character.user_id == user_id,
            Character.is_active == True,
        )
    )
    return result.scalar_one_or_none()


async def list_characters(user_id: str, db: AsyncSession) -> list[Character]:
    """List all active characters for a user."""
    result = await db.execute(
        select(Character).where(
            Character.user_id == user_id, Character.is_active == True
        )
    )
    return list(result.scalars().all())


async def delete_character(
    character_id: uuid.UUID, user_id: str, db: AsyncSession
) -> bool:
    """Soft delete a character."""
    character = await get_character(character_id, user_id, db)
    if not character:
        return False

    character.is_active = False
    await db.commit()
    return True
