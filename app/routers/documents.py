"""Document upload endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from pydantic import UUID4

from app.database import get_db
from app.schemas import DocumentUpload, DocumentResponse
from app.services import document_service

router = APIRouter()


def get_user_id(x_user_id: str = Header(..., description="User ID")) -> str:
    """Extract user ID from header (simplified auth)."""
    return x_user_id


@router.post("/{character_id}", response_model=DocumentResponse, status_code=201)
async def upload_document(
    character_id: UUID4,
    data: DocumentUpload,
    user_id: str = Depends(get_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a document to a character's knowledge base.

    Use this to give characters specialized knowledge, such as:
    - Teaching materials for instructor NPCs
    - Product manuals for shop keeper NPCs
    - Lore documents for storyteller NPCs
    - How-to guides for tutorial NPCs

    The character will reference these documents when responding.
    """
    try:
        document = await document_service.upload_document(
            character_id=character_id,
            user_id=user_id,
            filename=data.filename,
            content=data.content,
            description=data.description,
            db=db,
        )
        return document
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{character_id}", response_model=List[DocumentResponse])
async def list_documents(
    character_id: UUID4,
    user_id: str = Depends(get_user_id),
    db: AsyncSession = Depends(get_db),
):
    """List all documents for a character."""
    try:
        documents = await document_service.list_documents(character_id, user_id, db)
        return documents
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{document_id}", status_code=204)
async def delete_document(
    document_id: UUID4,
    user_id: str = Depends(get_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Delete a document."""
    success = await document_service.delete_document(document_id, user_id, db)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")
    return None
