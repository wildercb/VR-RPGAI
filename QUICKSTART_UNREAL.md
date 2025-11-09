# Quick Start: Test RPGAI in Unreal (5 Minutes)

This is the fastest way to test RPGAI with your Unreal VR game.

## Step 1: Start the Backend (1 minute)

```bash
cd /Users/wilder/dev/RPGAI
./start.sh
```

Wait for: `✓ RPGAI is starting!`

## Step 2: Create a Test Character (1 minute)

Open http://localhost:4020 in your browser:

1. Set **LLM Provider**: `ollama`
2. Set **Model**: Pick any model you have installed (e.g., `llama3.1`, `qwen2.5vl:3b`)
3. **Character Concept**: `A friendly blacksmith who sells weapons and remembers what I buy`
4. Click **Create Character**
5. Copy the **Character ID** (shown in the character list)

## Step 3: Test the API with Curl (30 seconds)

Replace `YOUR_CHARACTER_ID` with the ID from step 2:

```bash
curl -X POST http://localhost:4020/api/chat/send \
  -H "Content-Type: application/json" \
  -H "X-User-ID: test_player" \
  -d '{
    "character_id": "YOUR_CHARACTER_ID",
    "message": "Hello! What weapons do you have?"
  }'
```

You should get a JSON response with the character's reply!

## Step 4: Integrate with Unreal (3 minutes)

### Option A: Blueprint Quick Test

1. Open your Unreal project
2. Create a new **Actor Blueprint** called `BP_TestNPC`
3. Add this to the Event Graph:

**On BeginPlay:**
```
Event BeginPlay
  ↓
Print String: "Testing RPGAI..."
  ↓
Make HTTP Request (use HTTP Request node or VaRest plugin):
  - URL: http://localhost:4020/health
  - Method: GET
  ↓
On Complete:
  - Print response to screen
```

If you see `{"status":"healthy"}`, you're connected!

### Option B: Full Character Test (C++)

Add this to any Actor's BeginPlay:

```cpp
void AMyTestActor::BeginPlay()
{
    Super::BeginPlay();
    
    // Test connection
    TSharedRef<IHttpRequest> Request = FHttpModule::Get().CreateRequest();
    Request->SetURL(TEXT("http://localhost:4020/health"));
    Request->SetVerb(TEXT("GET"));
    Request->OnProcessRequestComplete().BindLambda(
        [](FHttpRequestPtr Req, FHttpResponsePtr Res, bool bSuccess)
        {
            if (bSuccess)
            {
                UE_LOG(LogTemp, Log, TEXT("RPGAI Connected: %s"), *Res->GetContentAsString());
            }
        });
    Request->ProcessRequest();
}
```

## Step 5: See Memory in Action (2 minutes)

Chat with your character multiple times:

**Message 1:**
```bash
curl -X POST http://localhost:4020/api/chat/send \
  -H "Content-Type: application/json" \
  -H "X-User-ID: test_player" \
  -d '{
    "character_id": "YOUR_CHARACTER_ID",
    "message": "I prefer swords over axes"
  }'
```

**Message 2 (later):**
```bash
curl -X POST http://localhost:4020/api/chat/send \
  -H "Content-Type: application/json" \
  -H "X-User-ID: test_player" \
  -d '{
    "character_id": "YOUR_CHARACTER_ID",
    "message": "What should I buy today?"
  }'
```

The character should remember you prefer swords!

## Step 6: View Memories

Click **"View Memories"** in the web UI to see exactly what the character learned about you!

## Full Integration

For complete Blueprint and C++ examples, see [UNREAL_INTEGRATION.md](UNREAL_INTEGRATION.md)

## Common Issues

**"Connection refused"**
- Make sure `./start.sh` is running
- Check http://localhost:4020 in your browser

**"No Ollama models"**
- Install Ollama: https://ollama.ai
- Run: `ollama pull llama3.1`

**Character responses are slow**
- Normal! Ollama takes 1-5 seconds
- Use smaller models like `phi3:mini` for faster responses
- Or use OpenRouter (cloud-based, faster)

## Next Steps

1. **Create multiple characters** - test different personalities
2. **Upload documents** - give NPCs specialized knowledge
3. **Test multi-user** - use different `X-User-ID` headers
4. **Integrate with VR controls** - voice input, hand gestures, etc.

See the full guide: [UNREAL_INTEGRATION.md](UNREAL_INTEGRATION.md)
