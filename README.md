# RPGAI - AI Character Agent System for Unreal VR

Create dynamic, evolving AI characters with simple prompts. Perfect for VR NPCs, instructors, and interactive agents in Unreal Engine.

## Features

- **Prompt-to-Character**: Create full AI characters from simple text prompts
- **Semantic Memory (Mem0)**: Characters remember and learn from every conversation
- **LLM Agnostic**: Supports Ollama (local/free) and OpenRouter (cloud)
- **Document Knowledge**: Upload documents for specialized character knowledge
- **Text-to-Speech (Piper)**: Natural voice synthesis with 20+ voice options
- **Speech-to-Text (Whisper)**: Local voice transcription supporting multiple audio formats
- **Universal Audio Support**: Automatic FFmpeg conversion for any audio format (WAV, MP3, WebM, OGG, etc.)
- **Game Context Integration**: Pass game state (location, inventory, quest progress) for contextual responses
- **Web UI**: Built-in testing interface for character creation, chat, and voice interaction
- **Easy Unreal Integration**: Simple REST API ready for VR/game engines

## Quick Start

### 1. Prerequisites

- Docker & Docker Compose
- (Optional) Ollama installed locally or OpenRouter API key

### 2. Setup

```bash
# Clone or navigate to project
cd RPGAI

# Copy environment file
cp .env.example .env

# Edit .env with your settings
# For Ollama (local, free):
DEFAULT_LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1

# OR for OpenRouter (cloud):
DEFAULT_LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=your_key_here
OPENROUTER_MODEL=meta-llama/llama-3.1-8b-instruct:free

# Start services
docker-compose up -d

# Check health
curl http://localhost:4020/health
```

### 3. Access the Web UI

Open your browser to **http://localhost:4020**

The web interface allows you to:
- Create characters from prompts
- Chat with characters in real-time (text or voice)
- Record voice messages and see automatic transcription
- Hear character responses with natural TTS voices
- View what characters remember about you
- Test the full API without code

### 4. Try the Interactive 3D Demo

Experience AI characters in a 3D environment: **http://localhost:4020/demo-room.html**

The interactive demo features:
- 3D room with customizable colors and furniture
- AI characters that autonomously move around
- Text and voice chat with characters
- Character voice responses with animations
- See [DEMO_ROOM.md](DEMO_ROOM.md) for details

### 5. Install Ollama Models (if using Ollama)

```bash
# Pull a model (if using local Ollama setup)
ollama pull llama3.1

# Or a smaller, faster model
ollama pull phi3:mini

# Note: By default, the system connects to Ollama on your host machine (http://host.docker.internal:11434)
```

## API Usage

For complete API documentation with Unreal C++, Python, and cURL examples, see [API_REFERENCE.md](API_REFERENCE.md).

### Create a Character

```bash
curl -X POST http://localhost:4020/api/characters \
  -H "Content-Type: application/json" \
  -H "X-User-ID: user123" \
  -d '{
    "prompt": "A wise medieval blacksmith who teaches players how to forge legendary swords"
  }'
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "user123",
  "name": "Gorin Ironhammer",
  "creation_prompt": "A wise medieval blacksmith...",
  "personality_summary": "Gorin is a gruff but kind-hearted master blacksmith with 40 years of experience...",
  "voice_id": "en_US-lessac-medium",
  "llm_provider": "ollama",
  "llm_model": "llama3.1",
  "created_at": "2025-11-08T10:30:00Z"
}
```

### List Your Characters

```bash
curl http://localhost:4020/api/characters \
  -H "X-User-ID: user123"
```

### Upload Knowledge Document

Give your character specialized knowledge:

```bash
curl -X POST http://localhost:4020/api/documents/550e8400-e29b-41d4-a716-446655440000 \
  -H "Content-Type: application/json" \
  -H "X-User-ID: user123" \
  -d '{
    "filename": "sword_forging_guide.txt",
    "content": "# Legendary Sword Forging\n\n## Materials Needed:\n- Damascus steel ingot\n- Dragon scale powder\n- Enchanted coal\n\n## Process:\n1. Heat forge to 2000°F...",
    "description": "Complete guide to forging legendary swords"
  }'
```

### Chat with Character (Text)

```bash
curl -X POST http://localhost:4020/api/chat/550e8400-e29b-41d4-a716-446655440000 \
  -H "Content-Type: application/json" \
  -H "X-User-ID: user123" \
  -d '{
    "message": "Hello! Can you teach me how to forge a legendary sword?",
    "game_context": {
      "location": "Ironhammer Forge",
      "player_level": 15,
      "player_inventory": ["iron_ore", "coal"]
    }
  }'
```

**Response:**
```json
{
  "conversation_id": "123e4567-e89b-12d3-a456-426614174000",
  "message": "Aye, welcome to me forge, young apprentice! *wipes soot from hands* Ye want to learn the ancient art of legendary sword forgin', do ye? Well, ye've come to the right place. First things first - do ye have yer materials ready? We'll be needin' Damascus steel, dragon scale powder, and enchanted coal. The process be demandin', but I'll guide ye every step of the way...",
  "audio_file": "/audio/550e8400-e29b-41d4-a716-446655440000_response.wav"
}
```

### Voice Interaction

**Transcribe Speech to Text:**
```bash
curl -X POST http://localhost:4020/api/chat/transcribe \
  -H "X-User-ID: user123" \
  -F "audio=@recording.wav"
```

**Response:**
```json
{
  "text": "Hello! Can you teach me how to forge a legendary sword?"
}
```

**Text to Speech:**
```bash
curl -X POST http://localhost:4020/api/tts \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Welcome to my forge!",
    "voice_id": "en_US-lessac-medium"
  }' \
  --output speech.wav
```

**Complete Voice Chat Flow:**
1. Record audio → STT → Transcribed text
2. Send text to character chat → Get response text
3. Convert response to speech → TTS → Audio file
4. Play audio in-game

See [VOICE_CHAT_INTEGRATION.md](VOICE_CHAT_INTEGRATION.md) for complete examples.

## Unreal Engine Integration

### HTTP REST Client (Blueprint)

1. Add **VaRest** plugin to your Unreal project (or use built-in HTTP module)

2. Create a character interaction blueprint:

```cpp
// Example Blueprint: Create Character
VaRest Request Node:
- URL: http://your-server:4020/api/characters
- Method: POST
- Headers:
  - Content-Type: application/json
  - X-User-ID: {YourPlayerID}
- Body:
{
  "prompt": "A mysterious wizard who teaches fire magic"
}

// On Success:
- Parse JSON response
- Store character_id in player save data
- Display character name to player
```

3. Chat with character and get voice response:

```cpp
// Example Blueprint: Send Message to NPC
VaRest Request Node:
- URL: http://your-server:4020/api/chat/{character_id}
- Method: POST
- Headers:
  - Content-Type: application/json
  - X-User-ID: {YourPlayerID}
- Body:
{
  "message": "{PlayerInputText}",
  "game_context": {
    "location": "Ancient Library",
    "player_level": 10,
    "time_of_day": "night"
  }
}

// On Success:
- Get "message" field for text display
- Get "audio_file" field for voice playback
- Download and play audio using Unreal's Sound Wave system
```

See [UNREAL_INTEGRATION.md](UNREAL_INTEGRATION.md) and [UNREAL_TTS_INTEGRATION.md](UNREAL_TTS_INTEGRATION.md) for complete integration guides.

### Example Unreal Blueprint Flow

```
Player Interacts with NPC
  ↓
Get Character ID from NPC Actor
  ↓
Get Player Input (Text or Voice Recording)
  ↓
[If Voice] POST to /api/chat/transcribe → Get Text
  ↓
HTTP POST to /api/chat/{character_id} with game context
  ↓
Wait for Response (includes text + audio_file path)
  ↓
Display Text in Dialogue Widget
  ↓
Download and Play TTS Audio Response
```

### C++ Integration Example

```cpp
// UCharacterChatComponent.h
UCLASS()
class UCharacterChatComponent : public UActorComponent
{
    GENERATED_BODY()

public:
    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    FString CharacterID;

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    FString ServerURL = "http://localhost:4020";

    UFUNCTION(BlueprintCallable)
    void SendMessage(FString Message);

private:
    void OnResponseReceived(FHttpRequestPtr Request, FHttpResponsePtr Response, bool bWasSuccessful);
};

// UCharacterChatComponent.cpp
void UCharacterChatComponent::SendMessage(FString Message)
{
    TSharedRef<IHttpRequest> Request = FHttpModule::Get().CreateRequest();
    Request->SetURL(FString::Printf(TEXT("%s/api/chat/%s"), *ServerURL, *CharacterID));
    Request->SetVerb("POST");
    Request->SetHeader("Content-Type", "application/json");
    Request->SetHeader("X-User-ID", "player123"); // Get from player session

    FString JsonBody = FString::Printf(TEXT("{\"message\":\"%s\"}"), *Message);
    Request->SetContentAsString(JsonBody);

    Request->OnProcessRequestComplete().BindUObject(this, &UCharacterChatComponent::OnResponseReceived);
    Request->ProcessRequest();
}

void UCharacterChatComponent::OnResponseReceived(FHttpRequestPtr Request, FHttpResponsePtr Response, bool bWasSuccessful)
{
    if (bWasSuccessful)
    {
        FString ResponseBody = Response->GetContentAsString();
        // Parse JSON and extract "message" field
        // Display in UI or play audio
    }
}
```

## Use Cases

### 1. VR Tutorial Instructor
```bash
{
  "prompt": "An enthusiastic VR fitness instructor who teaches players proper form for exercises"
}
# Upload documents: exercise_library.pdf, safety_guidelines.txt
```

### 2. Game Shop Keeper
```bash
{
  "prompt": "A cheerful merchant who sells potions and remembers customer preferences"
}
# Upload documents: item_catalog.json, pricing_guide.txt
```

### 3. Quest Giver NPC
```bash
{
  "prompt": "A mysterious hooded figure who gives cryptic clues about hidden treasures"
}
# Upload documents: game_lore.md, quest_database.txt
```

### 4. Language Tutor
```bash
{
  "prompt": "A patient Spanish teacher who helps players learn conversational Spanish in VR"
}
# Upload documents: spanish_vocabulary.txt, grammar_rules.pdf
```

## API Reference

### Base URL
```
http://localhost:4020
```

**Complete API Documentation:** [API_REFERENCE.md](API_REFERENCE.md)

### Authentication
Simple header-based auth (for production, implement proper JWT):
```
X-User-ID: your_user_identifier
```

### Endpoints

#### Characters
- `POST /api/characters` - Create character from prompt
- `GET /api/characters` - List all characters
- `GET /api/characters/{id}` - Get character details
- `DELETE /api/characters/{id}` - Delete character

#### Documents
- `POST /api/documents/{character_id}` - Upload document
- `GET /api/documents/{character_id}` - List documents
- `DELETE /api/documents/{document_id}` - Delete document

#### Chat
- `POST /api/chat/{character_id}` - Send message (returns text + audio)
- `GET /api/chat/{conversation_id}/history` - Get chat history

#### Voice
- `POST /api/chat/transcribe` - Transcribe audio to text (STT)
- `POST /api/tts` - Convert text to speech (TTS)
- `GET /api/tts/voices` - List available voices

### Health Check
```bash
curl http://localhost:4020/health
```

## Architecture

```
┌─────────────────┐
│  Unreal Engine  │
│   VR Client     │
└────────┬────────┘
         │ HTTP REST
         ↓
┌─────────────────────────────────┐
│     FastAPI Server (Port 4020)  │
│          (Python)               │
├─────────────────────────────────┤
│ • Character Generation          │
│ • Conversation + Memory (Mem0)  │
│ • Document Management           │
│ • Game Context Integration      │
│ • TTS/STT Orchestration         │
└────────┬────────────────────────┘
         │
    ┌────┴────┬─────────┬──────────┬──────────┐
    ↓         ↓         ↓          ↓          ↓
┌────────┐ ┌──────┐ ┌──────────┐ ┌──────┐ ┌────────┐
│Postgres│ │Redis │ │  Ollama  │ │Piper │ │Whisper │
│ (Data) │ │(Cache)│ │   LLM    │ │ TTS  │ │  STT   │
└────────┘ └──────┘ └──────────┘ └──────┘ └────────┘
                         │
                         ↓
                    ┌──────────┐
                    │OpenRouter│
                    │   API    │
                    └──────────┘
```

**Services:**
- **Backend (Port 4020)**: FastAPI application handling all logic
- **PostgreSQL**: Character data, conversations, documents
- **Redis**: Caching and session management
- **Piper TTS (Port 10200)**: Local text-to-speech via Wyoming protocol
- **Whisper STT (Port 10300)**: Local speech-to-text via Wyoming protocol
- **Ollama (Host:11434)**: Optional local LLM inference
- **OpenRouter**: Optional cloud LLM API

## Database Schema

```sql
characters
  - id (UUID)
  - user_id (string)
  - name (string)
  - creation_prompt (text)
  - system_prompt (text)
  - personality_summary (text)
  - llm_provider, llm_model

character_documents
  - id (UUID)
  - character_id (FK)
  - filename (string)
  - content (text)

conversations
  - id (UUID)
  - character_id (FK)
  - user_id (string)

messages
  - id (UUID)
  - conversation_id (FK)
  - role (user/assistant)
  - content (text)
  - audio_file (optional)
```

## Configuration

### LLM Providers

**Ollama (Local, Free)**
- Best for: Development, privacy, offline use
- Models: llama3.1, phi3:mini, mistral
- Setup: `docker-compose up ollama`

**OpenRouter (Cloud)**
- Best for: Production, variety of models
- Free tier available with rate limits
- Get API key: https://openrouter.ai

### Environment Variables

See [.env.example](.env.example) for all options.

## Roadmap

- [x] Text-to-Speech (Piper) integration ✅
- [x] Speech-to-Text (Whisper) integration ✅
- [x] Universal audio format support (FFmpeg) ✅
- [x] Game context integration ✅
- [ ] WebSocket real-time chat
- [ ] Voice activity detection
- [ ] Character emotion/animation hints
- [ ] Multi-character conversations
- [ ] Character personality evolution
- [ ] Vector database for better document search
- [ ] Unreal Engine plugin (C++)

## Documentation

- [API Reference](API_REFERENCE.md) - Complete API documentation with examples
- [Deployment Guide](DEPLOYMENT_GUIDE.md) - Deploy to production, data isolation, backups
- [Unreal Integration](UNREAL_INTEGRATION.md) - Integrate with Unreal Engine
- [Voice Chat Integration](VOICE_CHAT_INTEGRATION.md) - Complete voice chat workflow
- [TTS Quick Start](TTS_QUICK_START.md) - Text-to-speech guide
- [STT Quick Reference](STT_API_QUICK_REFERENCE.md) - Speech-to-text API guide
- [Game Context Guide](GAME_CONTEXT_GUIDE.md) - Pass game state to characters
- [Memory System](MEMORY_SYSTEM.md) - How character memory works
- [Web UI Guide](WEB_UI_GUIDE.md) - Using the web interface

## Data Privacy & Isolation

**Your data stays yours!** When you share this code:
- ✅ Your characters and conversations remain on your machine (in Docker volumes)
- ✅ Others get a fresh, empty database when they clone the repo
- ✅ Each deployment is completely isolated
- ✅ Database files are automatically excluded from git

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for details on data management, backups, and production deployment.

## License

MIT

## Contributing

PRs welcome! This is an early-stage project designed for easy Unreal VR integration.
