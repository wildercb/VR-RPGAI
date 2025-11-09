"""Chat and conversation endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Header, Query, UploadFile, File
from fastapi.responses import Response, FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from pydantic import UUID4, BaseModel

from app.database import get_db
from app.schemas import ChatRequest, ChatResponse, MessageResponse
from app.services import conversation_service_mem0 as conversation_service
from app.services.tts_service import tts_service
from app.services.stt_service import stt_service
from app.config import settings

router = APIRouter()


class TTSRequest(BaseModel):
    """Request model for TTS synthesis."""
    text: str
    voice: Optional[str] = None


class TranscriptionResponse(BaseModel):
    """Response model for STT transcription."""
    text: str


def get_user_id(x_user_id: str = Header(..., description="User ID")) -> str:
    """Extract user ID from header (simplified auth)."""
    return x_user_id


# ============================================================================
# TTS ENDPOINTS (Must be BEFORE /{character_id} catch-all route!)
# ============================================================================

@router.get("/synthesize")
async def synthesize_speech_get(
    text: str = Query(..., description="Text to synthesize")
):
    """Synthesize speech via GET request (Unreal-friendly)."""
    return await synthesize_speech(text=text)


@router.post("/synthesize")
async def synthesize_speech_post(tts_request: TTSRequest):
    """Synthesize speech via POST request."""
    return await synthesize_speech(text=tts_request.text)


# ============================================================================
# STT ENDPOINTS (Must be BEFORE /{character_id} catch-all route!)
# ============================================================================

@router.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(
    audio: UploadFile = File(..., description="Audio file to transcribe (WAV, MP3, etc.)", media_type="audio/*")
):
    """
    🎮 UNREAL-FRIENDLY STT ENDPOINT 🎮

    Transcribe audio to text using Faster-Whisper.

    **POST Request:**
    ```
    POST /api/chat/transcribe
    Content-Type: multipart/form-data

    audio: <audio file>
    ```

    **Returns:**
    ```json
    {
        "text": "transcribed text here"
    }
    ```

    **Usage in Unreal C++:**
    ```cpp
    // Create HTTP request
    TSharedRef<IHttpRequest> Request = FHttpModule::Get().CreateRequest();
    Request->SetURL("http://localhost:4020/api/chat/transcribe");
    Request->SetVerb("POST");

    // Add multipart form data
    FString Boundary = FString::Printf(TEXT("----Boundary%d"), FMath::Rand());
    Request->SetHeader("Content-Type", FString::Printf(TEXT("multipart/form-data; boundary=%s"), *Boundary));

    // Read audio file and add to form
    TArray<uint8> AudioData;
    FFileHelper::LoadFileToArray(AudioData, TEXT("path/to/recording.wav"));

    FString FormData = FString::Printf(
        TEXT("--%s\\r\\nContent-Disposition: form-data; name=\\"audio\\"; filename=\\"audio.wav\\"\\r\\nContent-Type: audio/wav\\r\\n\\r\\n"),
        *Boundary
    );
    // ... append audio data and closing boundary
    ```

    **Supported Audio Formats:** WAV (recommended), MP3, FLAC, OGG

    **Best Practices:**
    - Use WAV format for best compatibility (16kHz, 16-bit, mono)
    - Keep audio clips under 30 seconds for fast transcription
    - Use base-int8 model (default) for speed, or larger models for accuracy
    """
    from loguru import logger

    logger.info(f"Transcribe request received - filename: {audio.filename}, content_type: {audio.content_type}, size: {audio.size if hasattr(audio, 'size') else 'unknown'}")

    if not settings.STT_ENABLED:
        raise HTTPException(status_code=503, detail="STT is not enabled")

    if not stt_service:
        raise HTTPException(status_code=503, detail="STT service not initialized")

    try:
        # Read uploaded audio file
        audio_data = await audio.read()

        if not audio_data:
            raise HTTPException(status_code=400, detail="Empty audio file")

        # Detect audio format from filename
        audio_format = "wav"  # Default to WAV
        if audio.filename:
            if audio.filename.endswith(".mp3"):
                audio_format = "mp3"
            elif audio.filename.endswith(".flac"):
                audio_format = "flac"
            elif audio.filename.endswith(".ogg"):
                audio_format = "ogg"
            elif audio.filename.endswith(".webm"):
                audio_format = "webm"
            elif audio.filename.endswith(".m4a") or audio.filename.endswith(".mp4"):
                audio_format = "mp4"

        logger.info(f"Transcribing audio: format={audio_format}, size={len(audio_data)} bytes")

        # Transcribe audio
        transcript = await stt_service.transcribe(audio_data, audio_format)

        if not transcript:
            raise HTTPException(status_code=500, detail="Transcription failed")

        return TranscriptionResponse(text=transcript)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"STT transcription failed: {str(e)}")


# ============================================================================
# CHAT ENDPOINTS
# ============================================================================

@router.post("/send", response_model=ChatResponse)
async def send_message(
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
    - React to game context (location, weather, events, etc.)
    - Automatically learn new facts about you for future conversations

    Supports:
    - Player-to-NPC chat (normal mode)
    - NPC-to-NPC chat (set from_character_id)
    - Game context integration (location, weather, health, events)
    """
    if not hasattr(data, 'character_id') or not data.character_id:
        raise HTTPException(status_code=400, detail="character_id is required")

    try:
        # Convert context to dict if provided
        game_context_dict = None
        if data.context:
            game_context_dict = data.context.model_dump(exclude_none=True)

        response_text, conversation, audio_file = await conversation_service.send_message_with_memory(
            character_id=data.character_id,
            user_id=user_id,
            user_message=data.message,
            db=db,
            game_context=game_context_dict,
            from_character_id=data.from_character_id,
        )

        return ChatResponse(
            conversation_id=conversation.id,
            message=response_text,
            audio_file=audio_file,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{character_id}", response_model=ChatResponse)
async def send_message_legacy(
    character_id: UUID4,
    data: ChatRequest,
    user_id: str = Depends(get_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Legacy endpoint for backward compatibility."""
    data.character_id = character_id
    return await send_message(data=data, user_id=user_id, db=db)


async def synthesize_speech(text: str):
    """
    🎮 UNITY-FRIENDLY TTS ENDPOINT 🎮

    Synthesize text to speech and return WAV audio file.

    **Two ways to call this endpoint:**

    **GET Request (Simple):**
    ```
    GET /api/chat/synthesize?text=Hello%20world
    ```

    **POST Request (With Voice):**
    ```json
    POST /api/chat/synthesize
    {
        "text": "Hello world",
        "voice": "en_US-danny-low"
    }
    ```

    **Returns:** WAV audio file (audio/wav)

    **Usage in Unity C#:**
    ```csharp
    // Simple GET request
    string url = "http://localhost:4020/api/chat/synthesize?text=" + UnityWebRequest.EscapeURL("Hello!");
    UnityWebRequest request = UnityWebRequestMultimedia.GetAudioClip(url, AudioType.WAV);
    yield return request.SendWebRequest();
    AudioClip clip = DownloadHandlerAudioClip.GetContent(request);
    ```

    **Note:** Voice parameter currently not supported (uses default voice set in docker-compose.yml).
    Future update will support per-request voice selection with multiple Piper instances.
    """
    if not settings.TTS_ENABLED:
        raise HTTPException(status_code=503, detail="TTS is not enabled")

    if not text or not text.strip():
        raise HTTPException(status_code=400, detail="Text parameter is required")

    try:
        # Synthesize audio
        audio_path = await tts_service.synthesize(
            text=text,
            voice=None,  # Voice is set at Piper server level (docker-compose.yml)
            use_cache=True
        )

        if not audio_path:
            raise HTTPException(status_code=500, detail="TTS generation failed")

        # Return audio file directly
        import os
        if os.path.exists(audio_path):
            return FileResponse(
                path=audio_path,
                media_type="audio/wav",
                filename="speech.wav"
            )
        else:
            raise HTTPException(status_code=500, detail="Audio file not found")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS synthesis failed: {str(e)}")


@router.get("/test-tts")
async def test_tts():
    """Test TTS functionality with a sample message."""
    if not settings.TTS_ENABLED:
        raise HTTPException(status_code=503, detail="TTS is not enabled")

    try:
        test_text = "Hello! Text to speech is working perfectly. This is a test of the Piper TTS system."
        audio_path = await tts_service.synthesize(
            text=test_text,
            voice=None,
            use_cache=True
        )

        if not audio_path:
            raise HTTPException(status_code=500, detail="TTS generation failed")

        # Read the audio file and return it
        import os
        if os.path.exists(audio_path):
            with open(audio_path, 'rb') as f:
                audio_data = f.read()
            return Response(content=audio_data, media_type="audio/wav")
        else:
            raise HTTPException(status_code=500, detail="Audio file not found")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS test failed: {str(e)}")


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
