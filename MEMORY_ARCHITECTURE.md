# Memory Architecture Deep Dive

Complete explanation of how character and user memories are created, stored, and used.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     USER SENDS MESSAGE                           │
└────────────────────────┬────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│              STEP 1: SEMANTIC MEMORY RETRIEVAL                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  1. Embed user's message (384-dimensional vector)                │
│  2. Search pgvector database for similar memories                │
│  3. Retrieve:                                                     │
│     - Top 5 character-specific memories (this NPC about you)     │
│     - Top 3 user-global memories (all NPCs know about you)       │
│                                                                   │
└────────────────────────┬────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│              STEP 2: CONTEXT BUILDING                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Build LLM Context:                                              │
│  [System Prompt]                                                 │
│    - Character personality                                       │
│    - Uploaded documents (if any)                                 │
│    - CHARACTER MEMORIES (what NPC remembers about you)           │
│    - USER GLOBAL MEMORIES (facts all NPCs know)                  │
│  [Recent Messages] (last 5 only)                                 │
│  [Current User Message]                                          │
│                                                                   │
└────────────────────────┬────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│              STEP 3: LLM GENERATES RESPONSE                      │
└────────────────────────┬────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│              STEP 4: MEMORY EXTRACTION (Async)                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Mem0 analyzes the conversation turn:                            │
│  1. User message: "I'm Alex and I'm learning Python"             │
│  2. Assistant response: "Nice to meet you Alex..."               │
│                                                                   │
│  Mem0 LLM extracts:                                              │
│    ✓ "User's name is Alex"                                       │
│    ✓ "User is learning Python programming"                       │
│    ✓ "User is interested in software development"                │
│                                                                   │
│  Each memory:                                                    │
│    - Gets embedded (384-d vector)                                │
│    - Stored in PostgreSQL with pgvector                          │
│    - Tagged with character_id + user_id                          │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Memory Data Structures

### 1. Character Memory (Character-Specific)

**What it stores:** Facts this specific character learned about the user

**Database Table (Mem0 creates this):**
```sql
CREATE TABLE character_memories (
    id UUID PRIMARY KEY,
    character_id TEXT,      -- "character_abc-123"
    user_id TEXT,           -- "alex"
    agent_id TEXT,          -- "character_abc-123" (Mem0 format)

    memory TEXT,            -- "User's name is Alex"

    embedding vector(384),  -- Semantic vector for search

    created_at TIMESTAMP,
    metadata JSONB          -- {"conversation_id": "...", ...}
);

CREATE INDEX ON character_memories USING ivfflat (embedding vector_cosine_ops);
```

**Example Data:**
```json
{
  "id": "mem_001",
  "character_id": "character_abc-123",
  "user_id": "alex",
  "memory": "User is learning Python programming",
  "embedding": [0.234, -0.567, 0.123, ...], // 384 dimensions
  "created_at": "2025-11-08T10:30:00Z",
  "metadata": {
    "conversation_id": "conv_xyz",
    "timestamp": "2025-11-08T10:30:00Z"
  }
}
```

### 2. User Global Memory (Cross-Character)

**What it stores:** Facts about the user that ANY character can access

**How it works:**
- When Mem0 extracts memories without `agent_id`, they become global
- All characters can retrieve these when chatting with the same user

**Example Data:**
```json
{
  "id": "mem_global_001",
  "user_id": "alex",
  "agent_id": null,  // NULL = global memory
  "memory": "User lives in California",
  "embedding": [0.456, -0.234, 0.789, ...],
  "created_at": "2025-11-08T11:00:00Z"
}
```

## Memory Creation Process (Step-by-Step)

### Conversation Example

```
User: "Hi! I'm Alex and I'm learning Python for game development."
```

**Step 1: Message is sent to backend**

[app/services/conversation_service_mem0.py:37](app/services/conversation_service_mem0.py#L37)
```python
response_text, conversation = await conversation_service.send_message_with_memory(
    character_id=character_id,
    user_id="alex",
    user_message="Hi! I'm Alex and I'm learning Python for game development.",
    db=db
)
```

**Step 2: Semantic search for existing memories**

[app/services/conversation_service_mem0.py:88-106](app/services/conversation_service_mem0.py#L88-L106)
```python
# Retrieve relevant memories about this user
character_memories = memory_service.get_character_memories(
    character_id=str(character_id),
    user_id="alex",
    query="Hi! I'm Alex and I'm learning Python for game development.",  # Semantic search!
    limit=5
)

# Result: [] (first conversation, no memories yet)
```

**Step 3: Build context (no memories yet, just system prompt)**

```python
llm_messages = [
    {"role": "system", "content": "You are a helpful programming mentor..."},
    {"role": "user", "content": "Hi! I'm Alex and I'm learning Python for game development."}
]
```

**Step 4: LLM generates response**

```python
response = await llm_manager.generate(messages=llm_messages)
# Returns: "Hello Alex! Great to meet you. Python is perfect for game development..."
```

**Step 5: Save messages to database**

```python
# Save user message
user_msg = Message(
    conversation_id=conversation.id,
    role="user",
    content="Hi! I'm Alex and I'm learning Python for game development."
)

# Save assistant message
assistant_msg = Message(
    conversation_id=conversation.id,
    role="assistant",
    content="Hello Alex! Great to meet you..."
)
```

**Step 6: Extract memories (ASYNC - doesn't block response)**

[app/services/conversation_service_mem0.py:212-246](app/services/conversation_service_mem0.py#L212-L246)
```python
def _extract_memories_from_exchange(
    character_id="abc-123",
    user_id="alex",
    user_message="Hi! I'm Alex and I'm learning Python for game development.",
    assistant_message="Hello Alex! Great to meet you..."
):
    messages = [
        {"role": "user", "content": user_message},
        {"role": "assistant", "content": assistant_message}
    ]

    # Mem0 analyzes the conversation
    memory_service.add_character_memory(
        character_id="abc-123",
        user_id="alex",
        messages=messages,
        metadata={"conversation_id": "conv_xyz"}
    )
```

**Step 7: Mem0 extracts facts**

[app/services/memory_service.py:57-78](app/services/memory_service.py#L57-L78)

Mem0 internally does:
```python
# Mem0 uses its LLM to analyze the conversation
# It identifies:
extracted_memories = [
    "User's name is Alex",
    "User is learning Python programming",
    "User is interested in game development"
]

# For each memory:
for memory_text in extracted_memories:
    # 1. Generate embedding
    embedding = embed(memory_text)  # [0.234, -0.567, ...] 384 dims

    # 2. Store in PostgreSQL
    INSERT INTO character_memories (
        character_id,
        user_id,
        agent_id,
        memory,
        embedding,
        created_at,
        metadata
    ) VALUES (
        'character_abc-123',
        'alex',
        'character_abc-123',
        'User is learning Python programming',
        '[0.234, -0.567, ...]',
        NOW(),
        '{"conversation_id": "conv_xyz"}'
    )
```

## Memory Retrieval (Next Conversation)

### User returns and asks:

```
User: "Can you help me with async/await?"
```

**Step 1: Semantic Search**

[app/services/memory_service.py:92-117](app/services/memory_service.py#L92-L117)
```python
# Embed the query
query_embedding = embed("Can you help me with async/await?")
# [0.789, -0.234, 0.456, ...]

# Semantic search in PostgreSQL
SELECT
    memory,
    embedding <=> query_embedding AS distance
FROM character_memories
WHERE
    character_id = 'character_abc-123'
    AND user_id = 'alex'
ORDER BY embedding <=> query_embedding  -- Cosine similarity
LIMIT 5;
```

**Results (sorted by semantic similarity):**
```sql
memory                                      | distance
--------------------------------------------|---------
"User is learning Python programming"      | 0.12
"User is interested in game development"   | 0.34
"User's name is Alex"                      | 0.89
```

**Step 2: Build enriched context**

[app/services/conversation_service_mem0.py:88-127](app/services/conversation_service_mem0.py#L88-L127)
```python
system_content = """
You are a helpful programming mentor...

**What you remember about this user:**
- User is learning Python programming
- User is interested in game development
- User's name is Alex
"""

llm_messages = [
    {"role": "system", "content": system_content},
    {"role": "user", "content": "Can you help me with async/await?"}
]
```

**Step 3: LLM response (memory-aware!)**

```
LLM sees the memories and responds:
"Of course Alex! Let's work on async/await for your game development project..."
```

The character remembers Alex's name and context!

## Memory Data Examples

### Real Memory Objects

**Character Memory:**
```python
{
    "id": "mem_abc123",
    "memory": "User prefers dark fantasy game settings",
    "data": "User prefers dark fantasy game settings",  # Alias
    "metadata": {
        "character_id": "character_blacksmith_001",
        "conversation_id": "conv_xyz_789"
    },
    "created_at": "2025-11-08T14:30:00",
    "updated_at": "2025-11-08T14:30:00"
}
```

**User Global Memory:**
```python
{
    "id": "mem_global_456",
    "memory": "User is a game developer working in Unreal Engine",
    "metadata": {
        "learned_from_character_id": "character_wizard_002",
        "shared": true  # Accessible to all characters
    },
    "created_at": "2025-11-08T15:00:00"
}
```

## How Character Agents Use Memory

### In Conversation Service

[app/services/conversation_service_mem0.py:47-150](app/services/conversation_service_mem0.py#L47-L150)

```python
async def send_message_with_memory(character_id, user_id, user_message, db):
    # 1. Get character data
    character = await db.get(Character, character_id)

    # 2. RETRIEVE RELEVANT MEMORIES (semantic search)
    character_memories = memory_service.get_character_memories(
        character_id=str(character_id),
        user_id=user_id,
        query=user_message,  # Semantic search based on current message!
        limit=5
    )
    # Returns: [
    #   {"memory": "User is learning Python", ...},
    #   {"memory": "User prefers hands-on examples", ...}
    # ]

    user_global_memories = memory_service.get_user_global_memories(
        user_id=user_id,
        query=user_message,
        limit=3
    )
    # Returns: [
    #   {"memory": "User's name is Alex", ...},
    #   {"memory": "User is a game developer", ...}
    # ]

    # 3. BUILD CONTEXT with memories
    system_content = character.system_prompt

    # Add character-specific memories
    if character_memories:
        system_content += "\n\n**What you remember about this user:**\n"
        for mem in character_memories:
            system_content += f"- {mem['memory']}\n"

    # Add global memories
    if user_global_memories:
        system_content += "\n\n**General facts about this user:**\n"
        for mem in user_global_memories:
            system_content += f"- {mem['memory']}\n"

    # 4. GENERATE RESPONSE with memory context
    response = await llm_manager.generate([
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_message}
    ])

    # 5. EXTRACT NEW MEMORIES (async, non-blocking)
    _extract_memories_from_exchange(
        character_id, user_id,
        user_message, response.content
    )

    return response.content
```

## Memory Storage (PostgreSQL + pgvector)

### Database Tables Created by Mem0

**1. Memories Table:**
```sql
-- Mem0 creates this automatically
CREATE TABLE memories (
    id TEXT PRIMARY KEY,
    user_id TEXT,
    agent_id TEXT,  -- "character_abc-123" or NULL for global
    memory TEXT,
    embedding vector(384),  -- pgvector extension
    metadata JSONB,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Index for fast vector similarity search
CREATE INDEX ON memories
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Index for filtering
CREATE INDEX ON memories (user_id, agent_id);
```

**2. Query Example (What Mem0 does internally):**
```sql
-- Find memories semantically similar to query
SELECT
    id,
    memory,
    1 - (embedding <=> '[0.234, -0.567, ...]'::vector) AS similarity
FROM memories
WHERE
    user_id = 'alex'
    AND agent_id = 'character_abc-123'
ORDER BY embedding <=> '[0.234, -0.567, ...]'::vector
LIMIT 5;
```

**3. Results:**
```
id          | memory                           | similarity
------------|----------------------------------|----------
mem_001     | User is learning Python          | 0.92
mem_002     | User prefers hands-on examples   | 0.87
mem_003     | User's name is Alex              | 0.65
```

## API to View Memories

### GET /api/chat/{character_id}/memories

[app/routers/chat.py:74-91](app/routers/chat.py#L74-L91)

**Request:**
```bash
curl http://localhost:8000/api/chat/abc-123/memories \
  -H "X-User-ID: alex"
```

**Response:**
```json
{
  "enabled": true,
  "total_memories": 8,
  "memories": [
    {
      "id": "mem_001",
      "content": "User is learning Python programming",
      "created_at": "2025-11-08T10:30:00Z"
    },
    {
      "id": "mem_002",
      "content": "User prefers dark fantasy game settings",
      "created_at": "2025-11-08T11:15:00Z"
    },
    {
      "id": "mem_003",
      "content": "User's name is Alex",
      "created_at": "2025-11-08T10:31:00Z"
    }
  ]
}
```

## Memory Lifecycle

```
┌──────────────────────────────────────────────────────────┐
│  USER CONVERSATION                                        │
│  "Hi, I'm Alex and I love sci-fi games"                   │
└────────────────┬─────────────────────────────────────────┘
                 ↓
┌──────────────────────────────────────────────────────────┐
│  MEMORY EXTRACTION (Mem0 LLM analyzes)                    │
│  ✓ Extracts: "User's name is Alex"                        │
│  ✓ Extracts: "User enjoys sci-fi games"                   │
│  ✓ Generates embeddings                                   │
└────────────────┬─────────────────────────────────────────┘
                 ↓
┌──────────────────────────────────────────────────────────┐
│  STORAGE (PostgreSQL + pgvector)                          │
│  INSERT INTO memories (embedding, memory, user_id...)     │
└────────────────┬─────────────────────────────────────────┘
                 ↓
┌──────────────────────────────────────────────────────────┐
│  RETRIEVAL (Next conversation)                            │
│  User: "What kind of games do I like?"                    │
│                                                            │
│  SELECT memory FROM memories                               │
│  WHERE user_id = 'alex'                                    │
│  ORDER BY embedding <=> query_embedding                    │
│  LIMIT 5                                                   │
│                                                            │
│  Result: "User enjoys sci-fi games" ✓                      │
└────────────────┬─────────────────────────────────────────┘
                 ↓
┌──────────────────────────────────────────────────────────┐
│  CHARACTER RESPONSE (Memory-aware)                        │
│  "Based on our previous chat, I know you love sci-fi!"    │
└──────────────────────────────────────────────────────────┘
```

## Key Insights

1. **Character Memory vs User Memory:**
   - Character Memory: NPC-specific (blacksmith remembers what YOU told HIM)
   - User Memory: Global (all NPCs can access, like "User's name is Alex")

2. **Semantic Search:**
   - Memories aren't retrieved by keyword matching
   - Uses vector similarity (cosine distance)
   - Finds conceptually relevant memories

3. **Automatic Extraction:**
   - No manual memory creation needed
   - Mem0 LLM intelligently identifies facts
   - Happens after every conversation turn

4. **Efficient Context:**
   - Only retrieves top 5-8 most relevant memories
   - Reduced from 20 full messages
   - 67% token reduction

5. **Persistent:**
   - Memories never expire (unless deleted)
   - Work across sessions
   - Accessible from any device/platform

This is exactly what makes NPCs in VR feel alive—they genuinely remember you!