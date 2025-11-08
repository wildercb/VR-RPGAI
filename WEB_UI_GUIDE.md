# Web UI Guide

RPGAI includes a built-in web interface for testing and interacting with AI characters.

## Accessing the UI

**URL:** http://localhost:8000

The UI automatically loads when you visit the root URL of the RPGAI server.

## Features

### 1. Configuration Panel

**API URL:** The backend server URL (default: `http://localhost:8000`)
- Change this if running the backend on a different host/port
- Useful for testing from different devices on your network

**User ID:** Your unique identifier (default: `test_user`)
- Characters remember you by this ID
- Change it to test how characters interact with different users
- Memories are tied to this ID

### 2. Create Character

**Character Concept:** A simple text prompt describing your character

**Examples:**
```
"A wise wizard who teaches magic to beginners"
"A cheerful shopkeeper who sells potions and remembers customers"
"A gruff blacksmith who teaches swordsmithing"
"A patient Spanish tutor for VR language learning"
"A mysterious quest giver with cryptic clues"
```

**Process:**
1. Enter your character concept
2. Click "Create Character"
3. Wait 5-10 seconds while the LLM generates the full profile
4. Character appears in the sidebar with auto-generated name

### 3. Character List

Shows all your created characters with:
- Character name (LLM-generated)
- Personality summary
- Click to select and start chatting

**Refresh Button:** Reload the character list (useful if creating from API)

### 4. Chat Interface

**Features:**
- Real-time conversation with selected character
- Character avatar and user avatar
- Auto-scroll to latest message
- Memory-enhanced responses

**How it works:**
1. Select a character from the sidebar
2. Type your message in the input box
3. Press Enter or click "Send"
4. Character responds using:
   - Character personality
   - Uploaded documents
   - **Semantic memories about you**
   - Recent conversation context

### 5. View Memories

Click "View Memories" button to see:
- What the character remembers about you
- Facts extracted from conversations
- User preferences learned
- Total memory count

**Memory System:**
- Automatically extracts facts after each conversation
- Semantically searches for relevant memories
- Memories persist across sessions
- Can be shared across characters (global user facts)

## Testing Workflow

### Basic Test

1. **Create a character:**
   ```
   "A friendly programming mentor who helps with Python"
   ```

2. **Have a conversation:**
   ```
   User: "Hi! I'm Alex and I'm learning Python for game development."
   Character: "Hello Alex! Great to meet you..."

   User: "I'm stuck on async/await syntax"
   Character: *learns about your Python struggles*
   ```

3. **View Memories:**
   Click "View Memories" to see extracted facts:
   - "User's name is Alex"
   - "Learning Python"
   - "Interested in game development"
   - "Struggling with async/await"

4. **Test Recall (later):**
   ```
   User: "Can you help me with that async problem?"
   Character: "Of course Alex! Let's work on your async/await issue..."
   ```

### Advanced Test: Multiple Characters

1. **Create Character 1:**
   ```
   "A VR fitness instructor"
   ```

   Chat: "I want to lose weight and get fit"

2. **Create Character 2:**
   ```
   "A nutrition coach"
   ```

   Chat: "What should I eat?"

3. **Both characters can access global user memories:**
   - Character 2 might know about your fitness goals from Character 1

### Document Knowledge Test

Use the API to upload a document:

```bash
# Get character ID from the UI
CHAR_ID="your-character-id"

curl -X POST http://localhost:8000/api/documents/$CHAR_ID \
  -H "Content-Type: application/json" \
  -H "X-User-ID: test_user" \
  -d '{
    "filename": "python_guide.txt",
    "content": "Python async/await tutorial:\n1. async def creates coroutine\n2. await calls async function\n3. asyncio.run() runs event loop",
    "description": "Python async guide"
  }'
```

Then chat:
```
User: "How do I use async in Python?"
Character: *references the uploaded document*
```

## Unreal Integration Testing

The UI uses the **same API** that Unreal Engine would use:

### API Endpoints Used

1. **Create Character:**
   ```
   POST /api/characters
   Headers: X-User-ID
   Body: {"prompt": "..."}
   ```

2. **List Characters:**
   ```
   GET /api/characters
   Headers: X-User-ID
   ```

3. **Send Message:**
   ```
   POST /api/chat/{character_id}
   Headers: X-User-ID
   Body: {"message": "..."}
   ```

4. **View Memories:**
   ```
   GET /api/chat/{character_id}/memories
   Headers: X-User-ID
   ```

### Testing for Unreal

**What to test:**
1. **Character creation speed** - How long does LLM take?
2. **Response latency** - Chat response time for VR (should be <2s)
3. **Memory accuracy** - Does character recall facts correctly?
4. **Context relevance** - Are retrieved memories relevant to query?

**Network Testing:**
```javascript
// Test from browser console
fetch('http://localhost:8000/api/chat/YOUR_CHAR_ID', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-User-ID': 'test_user'
  },
  body: JSON.stringify({message: 'Hello!'})
})
.then(r => r.json())
.then(console.log)
```

## Troubleshooting

### Character Not Responding

**Check:**
1. API URL is correct (should match backend)
2. Backend is running (`docker ps` should show `rpgai-backend`)
3. Browser console for errors (F12 → Console)

### Memories Not Saving

**Check:**
1. `MEM0_ENABLE_MEMORY=true` in `.env`
2. Ollama has embedding model: `docker exec -it rpgai-ollama ollama pull nomic-embed-text`
3. pgvector extension enabled in PostgreSQL

### Slow Responses

**Optimize:**
1. Use smaller model: `OLLAMA_MODEL=phi3:mini`
2. Reduce temperature: Lower temperature = faster
3. Check system resources (CPU/RAM)

### CORS Errors

**If accessing from different domain:**

Add to `.env`:
```bash
CORS_ORIGINS=["http://localhost:3000", "http://your-ip:8000"]
```

Restart backend:
```bash
docker-compose restart backend
```

## Mobile Testing

The UI is responsive and works on mobile:

1. Find your computer's IP address:
   ```bash
   # macOS/Linux
   ifconfig | grep "inet "

   # Windows
   ipconfig
   ```

2. Update API URL in the UI to your IP:
   ```
   http://192.168.1.100:8000
   ```

3. Open on your phone's browser

## Voice Integration (Future)

The UI is designed to eventually support:
- Speech-to-Text input
- Text-to-Speech output (via Piper)
- Audio playback of character responses

This matches what Unreal VR would need for voice interactions.

## Developer Tools

**Browser Console:**
```javascript
// Access the API client
window.rpgaiClient

// Manually trigger API calls
rpgaiClient.apiRequest('/api/characters')

// Debug current character
console.log(rpgaiClient.currentCharacter)
```

**Network Tab:**
- Monitor all API requests
- Check response times
- Debug errors

## Next Steps

After testing in the UI:
1. Note the API patterns used
2. Implement the same patterns in Unreal C++/Blueprints
3. Use the same character IDs across platforms
4. Memories persist between UI and Unreal!

See [UNREAL_INTEGRATION.md](UNREAL_INTEGRATION.md) for Unreal implementation guide.
