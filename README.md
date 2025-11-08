# RPGAI - AI Character Agent System for Unreal VR

Create dynamic, evolving AI characters with simple prompts. Perfect for VR NPCs, instructors, and interactive agents in Unreal Engine.

## Features

- **Prompt-to-Character**: Create full AI characters from simple text prompts
- **Semantic Memory (Mem0)**: Characters remember and learn from every conversation
- **LLM Agnostic**: Supports Ollama (local/free) and OpenRouter (cloud)
- **Document Knowledge**: Upload documents for specialized character knowledge
- **Web UI**: Built-in testing interface for character creation and chat
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
curl http://localhost:8000/health
```

### 3. Access the Web UI

Open your browser to **http://localhost:8000**

The web interface allows you to:
- Create characters from prompts
- Chat with characters in real-time
- View what characters remember about you
- Test the full API without code

### 4. Install Ollama Models (if using Ollama)

```bash
# Pull a model
docker exec -it rpgai-ollama ollama pull llama3.1

# Or a smaller, faster model
docker exec -it rpgai-ollama ollama pull phi3:mini
```

## API Usage

### Create a Character

```bash
curl -X POST http://localhost:8000/api/characters \
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
curl http://localhost:8000/api/characters \
  -H "X-User-ID: user123"
```

### Upload Knowledge Document

Give your character specialized knowledge:

```bash
curl -X POST http://localhost:8000/api/documents/550e8400-e29b-41d4-a716-446655440000 \
  -H "Content-Type: application/json" \
  -H "X-User-ID: user123" \
  -d '{
    "filename": "sword_forging_guide.txt",
    "content": "# Legendary Sword Forging\n\n## Materials Needed:\n- Damascus steel ingot\n- Dragon scale powder\n- Enchanted coal\n\n## Process:\n1. Heat forge to 2000°F...",
    "description": "Complete guide to forging legendary swords"
  }'
```

### Chat with Character

```bash
curl -X POST http://localhost:8000/api/chat/550e8400-e29b-41d4-a716-446655440000 \
  -H "Content-Type: application/json" \
  -H "X-User-ID: user123" \
  -d '{
    "message": "Hello! Can you teach me how to forge a legendary sword?"
  }'
```

**Response:**
```json
{
  "conversation_id": "123e4567-e89b-12d3-a456-426614174000",
  "message": "Aye, welcome to me forge, young apprentice! *wipes soot from hands* Ye want to learn the ancient art of legendary sword forgin', do ye? Well, ye've come to the right place. First things first - do ye have yer materials ready? We'll be needin' Damascus steel, dragon scale powder, and enchanted coal. The process be demandin', but I'll guide ye every step of the way..."
}
```

## Unreal Engine Integration

### HTTP REST Client (Blueprint)

1. Add **VaRest** plugin to your Unreal project (or use built-in HTTP module)

2. Create a character interaction blueprint:

```cpp
// Example Blueprint: Create Character
VaRest Request Node:
- URL: http://your-server:8000/api/characters
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

3. Chat with character:

```cpp
// Example Blueprint: Send Message to NPC
VaRest Request Node:
- URL: http://your-server:8000/api/chat/{character_id}
- Method: POST
- Headers:
  - Content-Type: application/json
  - X-User-ID: {YourPlayerID}
- Body:
{
  "message": "{PlayerInputText}"
}

// On Success:
- Get "message" field from JSON
- Display in dialogue UI
- (Future) Play TTS audio response
```

### Example Unreal Blueprint Flow

```
Player Interacts with NPC
  ↓
Get Character ID from NPC Actor
  ↓
Get Player Input (Text or Voice-to-Text)
  ↓
HTTP POST to /api/chat/{character_id}
  ↓
Wait for Response
  ↓
Display Text in Dialogue Widget
  ↓
(Optional) Play TTS Audio
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
    FString ServerURL = "http://localhost:8000";

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
http://localhost:8000
```

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
- `POST /api/chat/{character_id}` - Send message
- `GET /api/chat/{conversation_id}/history` - Get chat history

### Health Check
```bash
curl http://localhost:8000/health
```

## Architecture

```
┌─────────────────┐
│  Unreal Engine  │
│   VR Client     │
└────────┬────────┘
         │ HTTP REST / WebSocket
         ↓
┌─────────────────┐
│  FastAPI Server │
│  (Python)       │
├─────────────────┤
│ Character Gen   │
│ Conversation    │
│ Document Mgmt   │
└────────┬────────┘
         │
    ┌────┴────┬─────────┐
    ↓         ↓         ↓
┌────────┐ ┌──────┐ ┌──────────┐
│Postgres│ │Ollama│ │OpenRouter│
│  DB    │ │ LLM  │ │   API    │
└────────┘ └──────┘ └──────────┘
```

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

- [ ] Text-to-Speech (Piper) integration
- [ ] WebSocket real-time chat
- [ ] Voice activity detection
- [ ] Character emotion/animation hints
- [ ] Multi-character conversations
- [ ] Character personality evolution
- [ ] Vector database for better document search
- [ ] Unreal Engine plugin (C++)

## License

MIT

## Contributing

PRs welcome! This is an early-stage project designed for easy Unreal VR integration.
