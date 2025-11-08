"""Document upload and management service."""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import Character, CharacterDocument
from loguru import logger
import uuid


async def upload_document(
    character_id: uuid.UUID,
    user_id: str,
    filename: str,
    content: str,
    description: Optional[str],
    db: AsyncSession,
) -> CharacterDocument:
    """
    Upload a document to a character's knowledge base.

    Args:
        character_id: ID of the character
        user_id: ID of the user (must own the character)
        filename: Name of the document
        content: Full text content of the document
        description: Optional description of what the document contains
        db: Database session

    Returns:
        Created CharacterDocument instance
    """
    # Verify character exists and belongs to user
    result = await db.execute(
        select(Character).where(
            Character.id == character_id,
            Character.user_id == user_id,
            Character.is_active == True,
        )
    )
    character = result.scalar_one_or_none()

    if not character:
        raise ValueError(f"Character {character_id} not found or access denied")

    # Create document
    document = CharacterDocument(
        id=uuid.uuid4(),
        character_id=character_id,
        filename=filename,
        content=content,
        description=description,
    )

    db.add(document)
    await db.commit()
    await db.refresh(document)

    logger.info(
        f"Document '{filename}' uploaded to character {character_id} ({len(content)} chars)"
    )

    return document


async def list_documents(
    character_id: uuid.UUID, user_id: str, db: AsyncSession
) -> list[CharacterDocument]:
    """List all documents for a character."""
    # Verify access
    result = await db.execute(
        select(Character).where(
            Character.id == character_id,
            Character.user_id == user_id,
            Character.is_active == True,
        )
    )
    character = result.scalar_one_or_none()

    if not character:
        raise ValueError(f"Character {character_id} not found or access denied")

    # Get documents
    result = await db.execute(
        select(CharacterDocument).where(CharacterDocument.character_id == character_id)
    )
    return list(result.scalars().all())


async def delete_document(
    document_id: uuid.UUID, user_id: str, db: AsyncSession
) -> bool:
    """Delete a document."""
    # Get document with character check
    result = await db.execute(
        select(CharacterDocument)
        .join(Character)
        .where(
            CharacterDocument.id == document_id,
            Character.user_id == user_id,
        )
    )
    document = result.scalar_one_or_none()

    if not document:
        return False

    await db.delete(document)
    await db.commit()

    logger.info(f"Document {document_id} deleted")
    return True
