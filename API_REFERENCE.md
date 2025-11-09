# RPGAI API Reference

Complete API documentation for integrating RPGAI Character Agent System into games, VR applications, and advanced platforms.

## Base URL

```
http://localhost:4020
```

## Authentication

All endpoints require a user identifier header:

```
X-User-ID: your_user_id
```

---

## 📋 Quick Reference

| Feature | Endpoint | Method | Description |
|---------|----------|--------|-------------|
| **Characters** | `/api/characters` | POST | Create AI character from prompt |
| | `/api/characters` | GET | List all characters |
| | `/api/characters/{id}` | GET | Get character details |
| | `/api/characters/{id}` | DELETE | Delete character |
| **Chat** | `/api/chat/send` | POST | Send message to character |
| | `/api/chat/{character_id}` | POST | Send message (legacy) |
| | `/api/chat/{conversation_id}/history` | GET | Get conversation history |
| | `/api/chat/{character_id}/memories` | GET | View character memories |
| **Documents** | `/api/documents/{character_id}` | POST | Upload knowledge document |
| | `/api/documents/{character_id}` | GET | List documents |
| | `/api/documents/{document_id}` | DELETE | Delete document |
| **TTS** | `/api/chat/synthesize` | GET/POST | Text-to-speech conversion |
| | `/api/chat/test-tts` | GET | Test TTS functionality |
| **STT** | `/api/chat/transcribe` | POST | Speech-to-text conversion |
| **Models** | `/api/models/providers` | GET | List LLM providers |
| | `/api/models/{provider}` | GET | List models for provider |
| **Health** | `/health` | GET | Service health check |

---

## 🎭 Character Management

### Create Character

Create an AI character from a text prompt.

**Endpoint:** `POST /api/characters`

**Headers:**
```
Content-Type: application/json
X-User-ID: player_123
```

**Request Body:**
```json
{
  "prompt": "A wise wizard who teaches fire magic in a mystical academy",
  "llm_provider": "ollama",
  "llm_model": "llama3.1"
}
```

**Response:** `201 Created`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "player_123",
  "name": "Eldrin the Flamekeep",
  "creation_prompt": "A wise wizard who teaches fire magic...",
  "system_prompt": "You are Eldrin the Flamekeep, a distinguished professor...",
  "personality_summary": "Eldrin is a patient and wise 300-year-old wizard...",
  "voice_id": "en_US-lessac-medium",
  "llm_provider": "ollama",
  "llm_model": "llama3.1",
  "created_at": "2025-11-08T10:30:00Z",
  "is_active": true
}
```

**Example (cURL):**
```bash
curl -X POST http://localhost:4020/api/characters \
  -H "Content-Type: application/json" \
  -H "X-User-ID: player_123" \
  -d '{
    "prompt": "A cheerful blacksmith who crafts legendary weapons"
  }'
```

**Example (Python):**
```python
import requests

response = requests.post(
    "http://localhost:4020/api/characters",
    headers={"X-User-ID": "player_123"},
    json={"prompt": "A mysterious fortune teller who sees the future"}
)

character = response.json()
print(f"Created: {character['name']} ({character['id']})")
```

**Example (Unreal C++):**
```cpp
TSharedRef<IHttpRequest> Request = FHttpModule::Get().CreateRequest();
Request->SetURL(TEXT("http://localhost:4020/api/characters"));
Request->SetVerb(TEXT("POST"));
Request->SetHeader(TEXT("Content-Type"), TEXT("application/json"));
Request->SetHeader(TEXT("X-User-ID"), TEXT("player_123"));

FString JsonBody = TEXT("{\"prompt\":\"A gruff orc warrior who trains recruits\"}");
Request->SetContentAsString(JsonBody);

Request->OnProcessRequestComplete().BindLambda([](
    FHttpRequestPtr Req, FHttpResponsePtr Res, bool bSuccess)
{
    if (bSuccess)
    {
        FString ResponseBody = Res->GetContentAsString();
        // Parse JSON and store character_id
    }
});

Request->ProcessRequest();
```

---

### List Characters

Get all characters for the current user.

**Endpoint:** `GET /api/characters`

**Headers:**
```
X-User-ID: player_123
```

**Response:** `200 OK`
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Eldrin the Flamekeep",
    "personality_summary": "A wise wizard...",
    "created_at": "2025-11-08T10:30:00Z"
  },
  {
    "id": "660e8400-e29b-41d4-a716-446655440001",
    "name": "Gorin Ironhammer",
    "personality_summary": "A gruff blacksmith...",
    "created_at": "2025-11-08T11:15:00Z"
  }
]
```

---

### Get Character Details

**Endpoint:** `GET /api/characters/{character_id}`

**Headers:**
```
X-User-ID: player_123
```

**Response:** `200 OK`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Eldrin the Flamekeep",
  "creation_prompt": "A wise wizard...",
  "system_prompt": "You are Eldrin...",
  "personality_summary": "Eldrin is...",
  "voice_id": "en_US-lessac-medium",
  "llm_provider": "ollama",
  "llm_model": "llama3.1",
  "created_at": "2025-11-08T10:30:00Z"
}
```

---

### Delete Character

**Endpoint:** `DELETE /api/characters/{character_id}`

**Headers:**
```
X-User-ID: player_123
```

**Response:** `200 OK`
```json
{
  "message": "Character deleted successfully"
}
```

---

## 💬 Chat & Conversation

### Send Message

Send a message to a character and get a response with optional TTS audio.

**Endpoint:** `POST /api/chat/send`

**Headers:**
```
Content-Type: application/json
X-User-ID: player_123
```

**Request Body:**
```json
{
  "character_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Can you teach me a fire spell?",
  "context": {
    "location": "Training Grounds",
    "time_of_day": "morning",
    "player_level": 5,
    "weather": "sunny",
    "recent_events": ["Completed beginner's quest", "Earned fire affinity"]
  },
  "from_character_id": null
}
```

**Response:** `200 OK`
```json
{
  "conversation_id": "123e4567-e89b-12d3-a456-426614174000",
  "message": "Ah, a eager student! *adjusts pointed hat* Very well, let us begin with the Flame Bolt spell. First, you must understand that fire magic requires both focus and respect for the element. Extend your dominant hand and visualize a sphere of flame...",
  "audio_file": "audio_cache/abc123def456.wav"
}
```

**Game Context Parameters:**

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `location` | string | Current game location | "Mystic Forest", "Castle Throne Room" |
| `time_of_day` | string | Game time | "dawn", "noon", "dusk", "night" |
| `weather` | string | Current weather | "sunny", "rainy", "stormy", "snowing" |
| `player_level` | integer | Player's level | 1-100 |
| `player_health` | float | Health percentage | 0.0-1.0 |
| `player_class` | string | Player class | "warrior", "mage", "rogue" |
| `recent_events` | array | Recent game events | ["Defeated dragon", "Found artifact"] |
| `nearby_characters` | array | Other characters present | ["Merchant", "Guard"] |
| `inventory_items` | array | Player's items | ["Health Potion", "Magic Sword"] |
| `active_quests` | array | Current quests | ["Find the Lost Tome"] |

**Example with Context (Python):**
```python
response = requests.post(
    "http://localhost:4020/api/chat/send",
    headers={"X-User-ID": "player_123"},
    json={
        "character_id": "550e8400-e29b-41d4-a716-446655440000",
        "message": "What should I do about the dragon?",
        "context": {
            "location": "Dragon's Lair Entrance",
            "time_of_day": "dusk",
            "player_level": 10,
            "player_health": 0.5,
            "recent_events": ["Escaped from dragon", "Lost half health"],
            "inventory_items": ["Healing Potion x3", "Fire Resistance Shield"]
        }
    }
)

data = response.json()
print(f"Character says: {data['message']}")
if data.get('audio_file'):
    print(f"Play audio: http://localhost:4020/{data['audio_file']}")
```

**Example (Unreal C++):**
```cpp
// Build JSON with game context
TSharedPtr<FJsonObject> JsonObject = MakeShareable(new FJsonObject);
JsonObject->SetStringField(TEXT("character_id"), CharacterID);
JsonObject->SetStringField(TEXT("message"), PlayerMessage);

// Add game context
TSharedPtr<FJsonObject> ContextObj = MakeShareable(new FJsonObject);
ContextObj->SetStringField(TEXT("location"), CurrentLocation);
ContextObj->SetStringField(TEXT("time_of_day"), TimeOfDay);
ContextObj->SetNumberField(TEXT("player_level"), PlayerLevel);
ContextObj->SetNumberField(TEXT("player_health"), PlayerHealth);

// Add recent events array
TArray<TSharedPtr<FJsonValue>> EventsArray;
for (const FString& Event : RecentEvents)
{
    EventsArray.Add(MakeShareable(new FJsonValueString(Event)));
}
ContextObj->SetArrayField(TEXT("recent_events"), EventsArray);

JsonObject->SetObjectField(TEXT("context"), ContextObj);

FString JsonString;
TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&JsonString);
FJsonSerializer::Serialize(JsonObject.ToSharedRef(), Writer);

// Send request
TSharedRef<IHttpRequest> Request = FHttpModule::Get().CreateRequest();
Request->SetURL(TEXT("http://localhost:4020/api/chat/send"));
Request->SetVerb(TEXT("POST"));
Request->SetHeader(TEXT("Content-Type"), TEXT("application/json"));
Request->SetHeader(TEXT("X-User-ID"), UserID);
Request->SetContentAsString(JsonString);
Request->ProcessRequest();
```

---

### Character-to-Character Chat

Enable NPCs to talk to each other!

**Request Body:**
```json
{
  "character_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Greetings, blacksmith! I need a new staff.",
  "from_character_id": "660e8400-e29b-41d4-a716-446655440001"
}
```

The receiving character will see: "Eldrin the Flamekeep says: Greetings, blacksmith! I need a new staff."

---

### Get Conversation History

**Endpoint:** `GET /api/chat/{conversation_id}/history?limit=50`

**Headers:**
```
X-User-ID: player_123
```

**Response:** `200 OK`
```json
[
  {
    "id": "msg_001",
    "role": "user",
    "content": "Hello!",
    "timestamp": "2025-11-08T10:35:00Z"
  },
  {
    "id": "msg_002",
    "role": "assistant",
    "content": "Greetings, young adventurer!",
    "audio_file": "audio_cache/xyz789.wav",
    "timestamp": "2025-11-08T10:35:02Z"
  }
]
```

---

### View Character Memories

See what the character remembers about the user.

**Endpoint:** `GET /api/chat/{character_id}/memories`

**Headers:**
```
X-User-ID: player_123
```

**Response:** `200 OK`
```json
{
  "enabled": true,
  "total_memories": 5,
  "memories": [
    {
      "id": "mem_001",
      "content": "User is a level 5 fire mage named Alex",
      "created_at": "2025-11-08T10:36:00Z"
    },
    {
      "id": "mem_002",
      "content": "User completed the Flame Bolt spell tutorial",
      "created_at": "2025-11-08T10:40:00Z"
    },
    {
      "id": "mem_003",
      "content": "User prefers direct teaching style over cryptic hints",
      "created_at": "2025-11-08T10:45:00Z"
    }
  ]
}
```

---

## 📚 Document Knowledge

### Upload Document

Give characters specialized knowledge from documents.

**Endpoint:** `POST /api/documents/{character_id}`

**Headers:**
```
Content-Type: application/json
X-User-ID: player_123
```

**Request Body:**
```json
{
  "filename": "fire_spells_compendium.txt",
  "content": "# Fire Magic Compendium\n\n## Flame Bolt\n- Level: Beginner\n- Mana Cost: 10\n- Damage: 25\n- Range: 30 meters\n...",
  "description": "Complete guide to fire magic spells"
}
```

**Response:** `201 Created`
```json
{
  "id": "doc_001",
  "character_id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "fire_spells_compendium.txt",
  "description": "Complete guide to fire magic spells",
  "uploaded_at": "2025-11-08T11:00:00Z"
}
```

---

### List Documents

**Endpoint:** `GET /api/documents/{character_id}`

**Headers:**
```
X-User-ID: player_123
```

**Response:** `200 OK`
```json
[
  {
    "id": "doc_001",
    "filename": "fire_spells_compendium.txt",
    "description": "Complete guide to fire magic spells",
    "uploaded_at": "2025-11-08T11:00:00Z"
  }
]
```

---

## 🔊 Text-to-Speech (TTS)

### Synthesize Speech

Convert text to speech audio (WAV format).

**Endpoint:** `GET /api/chat/synthesize`

**Query Parameters:**
- `text` (required): Text to synthesize

**Example:**
```bash
curl "http://localhost:4020/api/chat/synthesize?text=Hello%20adventurer" -o speech.wav
```

**Response:** `200 OK`
- Content-Type: `audio/wav`
- Returns 16kHz, 16-bit, mono WAV file

---

**Endpoint:** `POST /api/chat/synthesize`

**Request Body:**
```json
{
  "text": "Welcome to the academy!",
  "voice": "en_US-lessac-medium"
}
```

**Response:** `200 OK`
- Content-Type: `audio/wav`

**Example (Python):**
```python
response = requests.post(
    "http://localhost:4020/api/chat/synthesize",
    json={"text": "The dragon awakens!"}
)

with open("speech.wav", "wb") as f:
    f.write(response.content)
```

**Example (Unreal C++):**
```cpp
FString Text = TEXT("Greetings, warrior!");
FString EncodedText = FGenericPlatformHttp::UrlEncode(Text);
FString URL = FString::Printf(TEXT("http://localhost:4020/api/chat/synthesize?text=%s"), *EncodedText);

TSharedRef<IHttpRequest> Request = FHttpModule::Get().CreateRequest();
Request->SetURL(URL);
Request->SetVerb(TEXT("GET"));
Request->OnProcessRequestComplete().BindLambda([](
    FHttpRequestPtr Req, FHttpResponsePtr Res, bool bSuccess)
{
    if (bSuccess)
    {
        TArray<uint8> WAVData = Res->GetContent();
        USoundWave* SoundWave = CreateSoundWaveFromWAV(WAVData);
        PlaySound(SoundWave);
    }
});
Request->ProcessRequest();
```

---

## 🎤 Speech-to-Text (STT)

### Transcribe Audio

Convert audio to text using Faster-Whisper.

**Endpoint:** `POST /api/chat/transcribe`

**Headers:**
```
Content-Type: multipart/form-data
X-User-ID: player_123
```

**Form Data:**
- `audio` (file): Audio file (WAV, MP3, FLAC, OGG, WebM, etc.)

**Response:** `200 OK`
```json
{
  "text": "Hello wizard, can you teach me magic?"
}
```

**Supported Formats:**
- WAV (recommended - 16kHz, mono)
- MP3
- FLAC
- OGG
- WebM (browser MediaRecorder)
- AAC
- Any format supported by FFmpeg

**Example (cURL):**
```bash
curl -X POST http://localhost:4020/api/chat/transcribe \
  -H "X-User-ID: player_123" \
  -F "audio=@recording.wav"
```

**Example (Python):**
```python
with open("recording.wav", "rb") as f:
    response = requests.post(
        "http://localhost:4020/api/chat/transcribe",
        headers={"X-User-ID": "player_123"},
        files={"audio": f}
    )

transcription = response.json()
print(f"You said: {transcription['text']}")
```

**Example (JavaScript/Browser):**
```javascript
// Record audio from microphone
const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
const mediaRecorder = new MediaRecorder(stream);
const audioChunks = [];

mediaRecorder.ondataavailable = (event) => {
    audioChunks.push(event.data);
};

mediaRecorder.onstop = async () => {
    const audioBlob = new Blob(audioChunks);
    const formData = new FormData();
    formData.append('audio', audioBlob, 'recording.webm');

    const response = await fetch('http://localhost:4020/api/chat/transcribe', {
        method: 'POST',
        headers: { 'X-User-ID': 'player_123' },
        body: formData
    });

    const data = await response.json();
    console.log('Transcription:', data.text);
};

mediaRecorder.start();
// ... later ...
mediaRecorder.stop();
```

---

## 🎮 Complete Voice Chat Flow

Combine STT + Chat + TTS for full voice interaction:

**Example (Python):**
```python
# 1. Record audio (using your recording library)
audio_file = "player_voice.wav"

# 2. Transcribe speech to text
with open(audio_file, "rb") as f:
    stt_response = requests.post(
        "http://localhost:4020/api/chat/transcribe",
        headers={"X-User-ID": "player_123"},
        files={"audio": f}
    )
player_message = stt_response.json()["text"]
print(f"Player said: {player_message}")

# 3. Send to character
chat_response = requests.post(
    "http://localhost:4020/api/chat/send",
    headers={"X-User-ID": "player_123"},
    json={
        "character_id": "550e8400-e29b-41d4-a716-446655440000",
        "message": player_message
    }
)
data = chat_response.json()
character_response = data["message"]
audio_file = data.get("audio_file")

print(f"Character says: {character_response}")

# 4. Play TTS audio
if audio_file:
    audio_url = f"http://localhost:4020/{audio_file}"
    # Play audio in your application
```

---

## 🔧 Configuration & Models

### List LLM Providers

**Endpoint:** `GET /api/models/providers`

**Response:** `200 OK`
```json
{
  "providers": ["ollama", "openrouter"]
}
```

---

### List Models for Provider

**Endpoint:** `GET /api/models/ollama`

**Response:** `200 OK`
```json
{
  "models": [
    {
      "name": "llama3.1",
      "size": "4.7GB",
      "modified_at": "2025-11-08T10:00:00Z"
    },
    {
      "name": "phi3:mini",
      "size": "2.3GB",
      "modified_at": "2025-11-08T09:00:00Z"
    }
  ]
}
```

---

## ❤️ Health Check

**Endpoint:** `GET /health`

**Response:** `200 OK`
```json
{
  "status": "healthy",
  "services": {
    "database": "up",
    "redis": "up",
    "tts": "up",
    "stt": "up"
  }
}
```

---

## 🚨 Error Responses

All endpoints return standard HTTP status codes:

**400 Bad Request:**
```json
{
  "detail": "Missing required field: message"
}
```

**404 Not Found:**
```json
{
  "detail": "Character not found"
}
```

**500 Internal Server Error:**
```json
{
  "detail": "LLM provider unavailable"
}
```

**503 Service Unavailable:**
```json
{
  "detail": "TTS service is not enabled"
}
```

---

## 📖 See Also

- [README.md](README.md) - Getting started guide
- [UNREAL_INTEGRATION.md](UNREAL_INTEGRATION.md) - Unreal Engine integration
- [VOICE_CHAT_INTEGRATION.md](VOICE_CHAT_INTEGRATION.md) - Complete voice chat guide
- [GAME_CONTEXT_GUIDE.md](GAME_CONTEXT_GUIDE.md) - Game context examples
- [MEMORY_SYSTEM.md](MEMORY_SYSTEM.md) - How character memory works
