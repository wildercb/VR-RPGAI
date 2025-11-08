# Real Memory Data Examples

Concrete examples of how memories are stored and retrieved.

## Example 1: Simple Conversation

### Conversation
```
User (Alex): "Hi! I'm learning Python for VR game development."
NPC (Mentor): "Hello! Python is a great choice for game development..."
```

### Memories Extracted by Mem0

**Database Entries Created:**

```sql
-- Memory 1
INSERT INTO memories VALUES (
    id: 'mem_550e8400_1',
    user_id: 'alex',
    agent_id: 'character_mentor_001',
    memory: 'User is learning Python programming',
    embedding: [0.234, -0.567, 0.891, 0.123, ...], -- 384 dimensions
    metadata: '{"conversation_id": "conv_xyz", "category": "skill"}',
    created_at: '2025-11-08 10:30:00',
    updated_at: '2025-11-08 10:30:00'
);

-- Memory 2
INSERT INTO memories VALUES (
    id: 'mem_550e8400_2',
    user_id: 'alex',
    agent_id: 'character_mentor_001',
    memory: 'User is interested in VR game development',
    embedding: [0.456, -0.234, 0.678, 0.345, ...],
    metadata: '{"conversation_id": "conv_xyz", "category": "interest"}',
    created_at: '2025-11-08 10:30:01',
    updated_at: '2025-11-08 10:30:01'
);

-- Memory 3 (Global - no agent_id)
INSERT INTO memories VALUES (
    id: 'mem_550e8400_3',
    user_id: 'alex',
    agent_id: NULL,  -- NULL = global memory
    memory: "User's name is Alex",
    embedding: [0.789, -0.123, 0.456, 0.234, ...],
    metadata: '{"conversation_id": "conv_xyz", "category": "identity", "shared": true}',
    created_at: '2025-11-08 10:30:02',
    updated_at: '2025-11-08 10:30:02'
);
```

### API Response (GET /api/chat/mentor_001/memories)

```json
{
  "enabled": true,
  "total_memories": 3,
  "memories": [
    {
      "id": "mem_550e8400_1",
      "content": "User is learning Python programming",
      "created_at": "2025-11-08T10:30:00Z"
    },
    {
      "id": "mem_550e8400_2",
      "content": "User is interested in VR game development",
      "created_at": "2025-11-08T10:30:01Z"
    },
    {
      "id": "mem_550e8400_3",
      "content": "User's name is Alex",
      "created_at": "2025-11-08T10:30:02Z"
    }
  ]
}
```

---

## Example 2: Multi-Turn Conversation with Memory Retrieval

### Turn 1
```
User: "I'm working on a VR sword fighting game"
NPC: "That sounds exciting! What aspect are you focusing on?"
```

**Memories Extracted:**
- "User is developing a VR sword fighting game"
- "User is working on game development"

### Turn 2 (Days Later)
```
User: "Can you help me with combat mechanics?"
```

**Semantic Search Process:**

1. **Embed the query:**
   ```python
   query = "Can you help me with combat mechanics?"
   query_embedding = [0.567, -0.234, 0.789, ...]
   ```

2. **PostgreSQL Vector Search:**
   ```sql
   SELECT
       id,
       memory,
       1 - (embedding <=> '[0.567, -0.234, 0.789, ...]'::vector) AS similarity
   FROM memories
   WHERE
       user_id = 'alex'
       AND agent_id = 'character_mentor_001'
   ORDER BY embedding <=> '[0.567, -0.234, 0.789, ...]'::vector
   LIMIT 5;
   ```

3. **Results (sorted by relevance):**
   ```
   id              | memory                                    | similarity
   ----------------|-------------------------------------------|----------
   mem_fight_001   | User is developing a VR sword fighting... | 0.94
   mem_fight_002   | User is working on game development       | 0.82
   mem_python_001  | User is learning Python programming       | 0.45
   mem_name_001    | User's name is Alex                       | 0.21
   ```

4. **Context Built for LLM:**
   ```python
   system_prompt = """
   You are a helpful programming mentor...

   **What you remember about this user:**
   - User is developing a VR sword fighting game
   - User is working on game development
   - User is learning Python programming
   - User's name is Alex
   """
   ```

5. **NPC Response (memory-aware):**
   ```
   "Of course Alex! For combat mechanics in your VR sword fighting game,
   you'll want to focus on collision detection and physics..."
   ```

---

## Example 3: Cross-Character Memory Sharing

### Scenario: User talks to 2 different NPCs

**NPC 1: Shopkeeper**
```
User: "I need health potions. I'm a warrior class."
Shopkeeper: "Perfect! Here are warrior-specific potions..."
```

**Memories Stored:**
```json
{
  "id": "mem_shop_001",
  "user_id": "alex",
  "agent_id": "character_shopkeeper_001",
  "memory": "User plays as a warrior class"
},
{
  "id": "mem_shop_002",
  "user_id": "alex",
  "agent_id": null,  // GLOBAL MEMORY
  "memory": "User's character class is warrior"
}
```

**NPC 2: Quest Giver (Different Character)**
```
User: "What quests do you have?"
```

**Memory Retrieval for Quest Giver:**
```sql
-- Gets GLOBAL memories
SELECT * FROM memories
WHERE user_id = 'alex' AND agent_id IS NULL;

-- Returns: "User's character class is warrior"
```

**Quest Giver Response:**
```
"I have the perfect quest for a warrior like you!
The Dragon's Keep needs a strong fighter..."
```

The Quest Giver knows about your warrior class even though you never told them!

---

## Example 4: Memory Evolution Over Time

### Week 1
```
User: "I'm struggling with Python async"
```
**Memory:** "User is struggling with Python async programming"

### Week 2
```
User: "I finally figured out async/await!"
```
**Mem0 can UPDATE existing memory:**
```json
{
  "id": "mem_async_001",
  "memory": "User has learned Python async/await programming",
  "updated_at": "2025-11-15T10:30:00Z"  // Updated!
}
```

---

## Example 5: Complex User Profile

### After Multiple Conversations

**Character-Specific Memories (Programming Mentor):**
```json
[
  {
    "id": "mem_001",
    "memory": "User is learning Python for game development",
    "similarity": 0.95,
    "created_at": "2025-11-08"
  },
  {
    "id": "mem_002",
    "memory": "User prefers hands-on coding examples over theory",
    "similarity": 0.89,
    "created_at": "2025-11-09"
  },
  {
    "id": "mem_003",
    "memory": "User is building a VR sword fighting game",
    "similarity": 0.87,
    "created_at": "2025-11-10"
  },
  {
    "id": "mem_004",
    "memory": "User works better in the evening hours",
    "similarity": 0.72,
    "created_at": "2025-11-11"
  },
  {
    "id": "mem_005",
    "memory": "User has experience with Unity but new to Unreal",
    "similarity": 0.68,
    "created_at": "2025-11-12"
  }
]
```

**Global Memories (All Characters):**
```json
[
  {
    "id": "global_001",
    "memory": "User's name is Alex",
    "created_at": "2025-11-08"
  },
  {
    "id": "global_002",
    "memory": "User is a game developer",
    "created_at": "2025-11-08"
  },
  {
    "id": "global_003",
    "memory": "User lives in California",
    "created_at": "2025-11-09"
  }
]
```

---

## Example 6: Unreal VR Use Case

### VR Blacksmith NPC

**First Visit:**
```
Player (in VR): "Hi, I want to learn blacksmithing"
Blacksmith: "Welcome to my forge! I'm Gorin. Let's start with basics..."
```

**Memories Created:**
```json
[
  {
    "memory": "User wants to learn blacksmithing",
    "agent_id": "character_blacksmith_gorin"
  },
  {
    "memory": "This is user's first visit to the forge",
    "agent_id": "character_blacksmith_gorin"
  }
]
```

**Player Returns 2 Weeks Later:**
```
Player: "Hey Gorin, I'm back!"
```

**Memory Retrieved:**
```sql
SELECT memory FROM memories
WHERE user_id = 'player_123'
  AND agent_id = 'character_blacksmith_gorin'
ORDER BY embedding <=> query_embedding
LIMIT 5;
```

**Blacksmith Response (memory-aware):**
```
"Ah, welcome back! Last time you wanted to learn blacksmithing.
Ready to continue? We left off at basic metalwork..."
```

### Document Knowledge Combined with Memory

**Upload Blacksmithing Manual:**
```json
{
  "filename": "advanced_swordsmithing.txt",
  "content": "Damascus steel requires 1500°F heat and 100 folds..."
}
```

**Player asks:**
```
"How hot should the forge be for Damascus steel?"
```

**Context Built:**
```python
system_prompt = """
You are Gorin, a master blacksmith...

**Reference Documents:**
Damascus steel requires 1500°F heat and 100 folds...

**What you remember about this user:**
- User wants to learn blacksmithing
- User is interested in advanced techniques
"""
```

**Response combines memory + documents:**
```
"For Damascus steel, as we discussed, you'll need 1500°F.
Since you're still learning, let's start with something simpler first..."
```

---

## Example 7: Memory in JSON Format (Full Object)

### Complete Memory Object from Mem0

```json
{
  "id": "mem_550e8400-e29b-41d4-a716-446655440000",
  "user_id": "alex_player_001",
  "agent_id": "character_mentor_programming",
  "memory": "User is developing a VR RPG game in Unreal Engine 5",
  "hash": "a1b2c3d4e5f6",
  "metadata": {
    "character_id": "mentor_programming",
    "conversation_id": "conv_123abc",
    "timestamp": "2025-11-08T14:30:00Z",
    "category": "project",
    "importance": 0.9,
    "tags": ["vr", "game_dev", "unreal"]
  },
  "created_at": "2025-11-08T14:30:00.123456Z",
  "updated_at": "2025-11-08T14:30:00.123456Z",
  "embedding": [
    0.0234, -0.0567, 0.0891, 0.0123, -0.0456,
    // ... 379 more values (384 total)
    0.0789, -0.0234, 0.0456, 0.0678, -0.0123
  ],
  "score": 0.94,  // Similarity score when retrieved
  "data": "User is developing a VR RPG game in Unreal Engine 5"  // Alias for 'memory'
}
```

---

## Example 8: Memory Search Query (What Happens Under the Hood)

### User Message: "How do I optimize performance in VR?"

**Step 1: Embed the query**
```python
query_text = "How do I optimize performance in VR?"
query_embedding = embedding_model.encode(query_text)
# Result: [0.567, -0.234, 0.789, ...] (384 dimensions)
```

**Step 2: PostgreSQL Query (What Mem0 executes)**
```sql
WITH query_vector AS (
    SELECT '[0.567, -0.234, 0.789, ...]'::vector AS embedding
)
SELECT
    m.id,
    m.memory,
    m.metadata,
    m.created_at,
    1 - (m.embedding <=> q.embedding) AS similarity_score
FROM memories m, query_vector q
WHERE
    m.user_id = 'alex'
    AND (
        m.agent_id = 'character_mentor_001'
        OR m.agent_id IS NULL  -- Include global memories
    )
ORDER BY m.embedding <=> q.embedding  -- Cosine distance
LIMIT 8;
```

**Step 3: Results**
```
memory                                           | similarity | created_at
-------------------------------------------------|------------|------------
User is developing a VR RPG game                 | 0.96       | 2025-11-08
User is interested in VR game optimization       | 0.91       | 2025-11-10
User has experience with Unity performance       | 0.78       | 2025-11-09
User is using Unreal Engine 5                    | 0.72       | 2025-11-08
User prefers hands-on examples                   | 0.54       | 2025-11-09
User's name is Alex                              | 0.23       | 2025-11-08
```

**Step 4: Top 5 memories used in context**
```python
relevant_memories = [
    "User is developing a VR RPG game",
    "User is interested in VR game optimization",
    "User has experience with Unity performance",
    "User is using Unreal Engine 5",
    "User prefers hands-on examples"
]
```

---

## Key Takeaways

1. **Memories are NOT keywords** - They're semantic vectors
2. **Retrieval is intelligent** - Finds conceptually similar content
3. **Storage is efficient** - Only relevant memories loaded
4. **Evolution happens** - Memories can be updated over time
5. **Sharing works** - Global memories accessible to all characters

This creates truly **intelligent NPCs** that remember and learn from every interaction!
