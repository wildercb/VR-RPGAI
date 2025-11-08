# Semantic Memory System with Mem0

RPGAI uses **Mem0.ai** for sophisticated semantic memory management, allowing characters to remember users across conversations and evolve over time.

## Overview

### Traditional Approach (Before)
- Store last 20 messages
- Load all 20 messages into every request
- No understanding of what's important
- Memory doesn't evolve

### Semantic Memory Approach (Now)
- **Extract** meaningful facts from conversations
- **Store** with semantic embeddings
- **Retrieve** only relevant memories at inference time
- **Evolve** character understanding over time

## Architecture

```
User sends message
    ↓
Semantic Search: Find relevant memories (5 character-specific + 3 global)
    ↓
Context Building:
  - Character system prompt
  - Uploaded documents
  - Relevant semantic memories ← MAGIC HERE
  - Last 5 recent messages (reduced from 20!)
    ↓
LLM generates response
    ↓
Save message + Extract new memories asynchronously
```

## Memory Types

### 1. Character Memories
Specific to one character-user relationship:
- "User prefers to be called 'Doc'"
- "User is learning Python and struggling with async"
- "User mentioned they're a game developer"

### 2. User Global Memories
Facts that span across ALL characters:
- "User's name is Alex"
- "User lives in California"
- "User has a dog named Max"

## How It Works

### Memory Extraction
After each conversation turn, Mem0 automatically extracts:
- **User facts**: Things about the user
- **Preferences**: User's likes/dislikes
- **Events**: Important happenings
- **Character reflections**: What the character learned

### Semantic Retrieval
When you chat, the system:
1. Embeds your current message
2. Searches for semantically similar memories
3. Pulls top 5 character memories + top 3 global memories
4. Adds them to context

**Example:**
```python
User: "Can you help me with that Python problem from last week?"

Semantic Search finds:
- "User is learning Python async programming"
- "User was stuck on await syntax"
- "User is building a VR game backend"

Character responds with relevant context!
```

## API Usage

### Chat with Memory
```bash
curl -X POST http://localhost:8000/api/chat/{character_id} \
  -H "Content-Type: application/json" \
  -H "X-User-ID: alex123" \
  -d '{"message": "Hey, remember what I told you about my project?"}'
```

Response will include relevant memories automatically.

### View What Character Remembers
```bash
curl http://localhost:8000/api/chat/{character_id}/memories \
  -H "X-User-ID: alex123"
```

Response:
```json
{
  "enabled": true,
  "total_memories": 12,
  "memories": [
    {
      "id": "mem_abc123",
      "content": "User is working on a VR RPG game in Unreal Engine",
      "created_at": "2025-11-08T10:30:00Z"
    },
    {
      "id": "mem_def456",
      "content": "User prefers characters with detailed backstories",
      "created_at": "2025-11-08T11:15:00Z"
    }
  ]
}
```

## Configuration

### Enable/Disable Memory

**.env:**
```bash
MEM0_ENABLE_MEMORY=true  # Set to false to disable
```

### Choose LLM for Memory Extraction

Mem0 uses an LLM to extract memories. You can use:

**Option 1: Ollama (Local, Free)**
```bash
MEM0_LLM_PROVIDER=ollama
MEM0_LLM_MODEL=llama3.1
```

**Option 2: OpenRouter (Cloud)**
```bash
MEM0_LLM_PROVIDER=openrouter
MEM0_LLM_MODEL=meta-llama/llama-3.1-8b-instruct:free
OPENROUTER_API_KEY=your_key
```

## Setup Instructions

### 1. Install Ollama Embedding Model

For local embeddings (required when using Ollama):

```bash
docker exec -it rpgai-ollama ollama pull nomic-embed-text
```

### 2. Verify pgvector Extension

Connect to PostgreSQL:
```bash
docker exec -it rpgai-postgres psql -U rpgai -d rpgai
```

Check extension:
```sql
\dx
-- Should show "vector" extension

SELECT * FROM pg_extension WHERE extname = 'vector';
```

### 3. Test Memory System

**Create a character:**
```bash
curl -X POST http://localhost:8000/api/characters \
  -H "Content-Type: application/json" \
  -H "X-User-ID: alex" \
  -d '{"prompt": "A helpful programming mentor"}'
```

**Have a conversation with facts:**
```bash
# Message 1: Share information
curl -X POST http://localhost:8000/api/chat/{char_id} \
  -H "X-User-ID: alex" \
  -d '{"message": "Hi! My name is Alex and I am learning Python for game development."}'

# Message 2: Test recall
curl -X POST http://localhost:8000/api/chat/{char_id} \
  -H "X-User-ID: alex" \
  -d '{"message": "What do you remember about me?"}'
```

The character should recall your name and interests!

**View extracted memories:**
```bash
curl http://localhost:8000/api/chat/{char_id}/memories \
  -H "X-User-ID: alex"
```

## Benefits

### For VR NPCs

**Immersive Interactions:**
```
Player (first visit): "Hi, I'm looking to learn swordsmithing."
NPC: "Welcome! I'm Gorin. Let me teach you the basics..."

Player (returns weeks later): "Hey Gorin, can we continue my training?"
NPC: "Ah, welcome back! Last time we covered Damascus steel forging.
      Ready to move on to enchanted weapons?"
```

### For Tutorial Characters

**Personalized Learning:**
```
Student: "I'm confused about async/await"
Tutor: *Retrieves: "Student struggled with callbacks last session"*
Tutor: "Let me explain async/await in terms of those callbacks we discussed..."
```

### Cross-Character Memory

**Shared Context:**
```
# Talk to Shopkeeper
User: "I need healing potions"
Shopkeeper: *Learns: User plays as a warrior*

# Later, talk to Quest Giver
User: "What quests do you have?"
Quest Giver: *Accesses global memory: User is a warrior*
Quest Giver: "I have a perfect quest for a warrior like you..."
```

## Advanced Usage

### Programmatic Memory Management

**Python Example:**
```python
from app.services.memory_service import memory_service

# Add specific memory manually
memory_service.add_character_memory(
    character_id="char_123",
    user_id="alex",
    messages=[{
        "role": "user",
        "content": "I prefer dark fantasy settings"
    }],
    metadata={"type": "preference"}
)

# Search memories semantically
memories = memory_service.get_character_memories(
    character_id="char_123",
    user_id="alex",
    query="What does the user like?",
    limit=10
)
```

### Update Memory
```python
memory_service.update_memory(
    memory_id="mem_abc123",
    data="User is now proficient in Python async programming"
)
```

### Delete Memories
```python
# Delete specific memory
memory_service.delete_memory("mem_abc123")

# Delete all memories for a character-user pair
memory_service.delete_all_character_memories(
    character_id="char_123",
    user_id="alex"
)
```

## Performance Considerations

### Token Efficiency
- **Before**: 20 messages × ~100 tokens = 2000 tokens
- **After**: 5 messages + 8 memories × ~20 tokens = 660 tokens
- **Savings**: ~67% reduction in context tokens

### Response Time
- Semantic search: ~50-100ms
- Memory extraction: Async (doesn't block response)
- Net effect: Faster responses!

## Troubleshooting

### Memories Not Being Extracted

**Check Mem0 is initialized:**
```bash
docker logs rpgai-backend | grep "Mem0"
# Should see: "Mem0 initialized successfully"
```

**Check pgvector:**
```sql
SELECT * FROM pg_available_extensions WHERE name = 'vector';
```

**Verify LLM is running:**
```bash
# For Ollama
curl http://localhost:11434/api/tags

# For OpenRouter
curl https://openrouter.ai/api/v1/models \
  -H "Authorization: Bearer $OPENROUTER_API_KEY"
```

### Embeddings Not Working

**Pull embedding model:**
```bash
docker exec -it rpgai-ollama ollama pull nomic-embed-text
```

**Test embedding:**
```bash
curl http://localhost:11434/api/embeddings \
  -d '{"model": "nomic-embed-text", "prompt": "test"}'
```

### Memory Not Retrieving

**Check memory count:**
```bash
curl http://localhost:8000/api/chat/{char_id}/memories \
  -H "X-User-ID: your_user_id"
```

If empty, have a few conversations first to build memory.

## Comparison: Before vs After

### Before (Basic Context Window)
```python
def send_message():
    # Load last 20 messages
    messages = get_last_20_messages()

    # Send all to LLM
    response = llm.generate(messages)

    return response
```

**Problems:**
- All 20 messages always loaded (irrelevant data)
- No understanding of importance
- Forgets after 20 messages
- High token usage

### After (Semantic Memory)
```python
def send_message_with_memory():
    # Semantic search for relevant memories
    memories = memory_service.search(query=current_message, limit=5)

    # Only last 5 messages
    recent = get_last_5_messages()

    # Build enriched context
    context = system_prompt + memories + documents + recent

    response = llm.generate(context)

    # Extract new memories (async)
    extract_memories_async(conversation)

    return response
```

**Benefits:**
- Only relevant information retrieved
- Memories persist forever
- Semantic understanding
- Lower token usage
- Better responses

## Future Enhancements

- [ ] Memory importance decay over time
- [ ] Memory consolidation (merge similar memories)
- [ ] Emotional tagging of memories
- [ ] Memory visualization in UI
- [ ] Multi-modal memories (images, audio)
- [ ] Memory sharing between character groups

## Learn More

- [Mem0 Documentation](https://docs.mem0.ai)
- [Mem0 GitHub](https://github.com/mem0ai/mem0)
- [pgvector Documentation](https://github.com/pgvector/pgvector)
- [Semantic Search Explained](https://www.pinecone.io/learn/what-is-semantic-search/)

---

**Ready to try it?** Start the system and have a conversation - watch as your characters learn and remember!

```bash
./start.sh
```
