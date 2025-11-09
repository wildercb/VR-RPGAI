# 🔊 TTS Feature - Quick Start Guide

## ✅ System is Ready!

All services are running:
- ✅ Backend (http://localhost:4020)
- ✅ Piper TTS (http://localhost:10200)
- ✅ PostgreSQL Database
- ✅ Redis Cache
- ✅ Ollama LLM

## 🎯 How to Use TTS

### Step 1: Open the Web UI

Go to: **http://localhost:4020**

### Step 2: Clear Browser Cache

**IMPORTANT**: Your browser may have cached the old JavaScript without audio support.

**Quick Fix:**
- **Mac**: Press `Cmd + Shift + R`
- **Windows/Linux**: Press `Ctrl + Shift + F5`

Or in DevTools (F12):
- Go to Network tab
- Check "Disable cache"
- Reload page

### Step 3: Verify TTS is Enabled

Look for the **green badge** at the top:
```
🎮 RPGAI Character Testing Interface 🔊 TTS Enabled
```

The description should say:
```
Create and interact with AI characters powered by semantic memory.
Character responses include voice audio!
```

### Step 4: Create a Character

1. In the left sidebar, under "➕ Create Character"
2. Enter a character concept, for example:
   ```
   A wise old wizard who speaks slowly and mysteriously
   ```
3. Select **ollama** as provider
4. Select **llama3.1** as model
5. Click **Create Character**

### Step 5: Start Chatting

1. Click on your character in the character list
2. Type a message in the chat input:
   ```
   Hello! Tell me about yourself.
   ```
3. Press Enter or click **Send**

### Step 6: Listen to the Audio!

**What You'll See:**
1. Character's text response appears
2. A **🔊 Play** button appears next to the message
3. **Audio plays automatically!**
4. Click the 🔊 button to replay anytime

## 🎬 Visual Example

```
┌─────────────────────────────────────────┐
│ Chat Messages                           │
├─────────────────────────────────────────┤
│                                         │
│  You: Hello! Tell me about yourself.   │
│                                         │
│  🧙 Wizard:                             │
│  Greetings, young one. I am Eldrin,    │
│  keeper of ancient knowledge...        │
│                        [🔊 Play]        │
│                                         │
└─────────────────────────────────────────┘
```

## 🔍 How to Verify It's Working

### Check 1: Browser Console

Open DevTools (F12) → Console tab

You should see:
```
loadCharacters() called
Loaded characters: 1 ["Wizard"]
Playing audio: /audio_cache/abc123def456.wav
```

### Check 2: Audio Files

Check the audio cache directory:
```bash
ls -lh /Users/wilder/dev/RPGAI/audio_cache/
```

You should see WAV files:
```
-rw-r--r--  1 user  staff   156K Nov  8 14:30 abc123def456.wav
-rw-r--r--  1 user  staff   203K Nov  8 14:31 789ghi012jkl.wav
```

### Check 3: Direct Audio Access

After getting a response, try accessing the audio directly:
```
http://localhost:4020/audio_cache/abc123def456.wav
```

It should play or download the WAV file.

### Check 4: Backend Logs

```bash
docker-compose logs backend --tail 20 | grep "TTS"
```

Should show:
```
Generated TTS audio: audio_cache/abc123def456.wav
```

## 🎨 Features

### Automatic Audio Generation
- **Every character response** gets TTS audio
- Audio is **cached** (same text = reused file)
- **Instant playback** for cached responses

### Audio Controls
- **Auto-play**: Audio plays automatically when response arrives
- **Manual play**: Click 🔊 button to replay
- **Stop previous**: New audio stops any currently playing audio

### Multi-Agent Support
- Works with **character-to-character** conversations
- Each character gets their own audio
- **🔊 Play buttons** on all character messages

### Game Context Integration
- TTS works with **all game context** features
- Location, weather, events all included in responses
- Audio generated for context-aware responses

## 🛠️ Troubleshooting

### Problem: No 🔊 Play Button

**Solution 1**: Hard refresh browser
```
Mac: Cmd + Shift + R
Windows: Ctrl + Shift + F5
```

**Solution 2**: Clear browser cache completely
```
Chrome: Settings → Privacy → Clear browsing data
```

**Solution 3**: Check browser console for errors
```
F12 → Console tab
Look for JavaScript errors
```

### Problem: Audio Doesn't Play

**Solution 1**: Check browser audio settings
- Browser not muted?
- System volume up?

**Solution 2**: Test audio file directly
```
http://localhost:4020/audio_cache/{filename}.wav
```

**Solution 3**: Check Piper service
```bash
docker-compose logs piper
```

Should show: `INFO:__main__:Ready`

### Problem: Slow Audio Generation

**First response**: 2-5 seconds (normal - generating audio)
**Cached responses**: Instant (reusing existing audio)

If consistently slow:
```bash
docker-compose logs piper --tail 50
```

Look for errors or download messages.

## 🚀 Advanced Usage

### Test via API

Create a character and chat via command line:

```bash
# 1. Create character
CHAR_ID=$(curl -s -X POST "http://localhost:4020/api/characters" \
  -H "Content-Type: application/json" \
  -H "X-User-ID: testuser" \
  -d '{
    "prompt": "A friendly robot",
    "llm_provider": "ollama",
    "llm_model": "llama3.1"
  }' | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")

echo "Character ID: $CHAR_ID"

# 2. Send message and get audio
curl -s -X POST "http://localhost:4020/api/chat/send" \
  -H "Content-Type: application/json" \
  -H "X-User-ID: testuser" \
  -d "{
    \"character_id\": \"$CHAR_ID\",
    \"message\": \"Hello, introduce yourself\"
  }" | python3 -m json.tool
```

Look for:
```json
{
  "conversation_id": "...",
  "message": "Hello! I'm a friendly robot...",
  "audio_file": "audio_cache/abc123.wav"
}
```

### Download Audio

```bash
# Get the audio_file path from above, then:
curl -O "http://localhost:4020/audio_cache/abc123.wav"

# Play it (Mac):
afplay abc123.wav

# Or open in browser:
open "http://localhost:4020/audio_cache/abc123.wav"
```

### Change Voice

Edit `docker-compose.yml`:
```yaml
piper:
  command: --voice en_US-amy-medium  # Change this
```

Available voices:
- `en_US-lessac-medium` (default - neutral, clear)
- `en_US-amy-medium` (female, expressive)
- `en_US-joe-medium` (male, casual)
- `en_GB-alan-medium` (British, formal)

Then restart:
```bash
docker-compose restart piper
```

## 📊 Performance

- **Generation**: 2-5 seconds for new text
- **Cache hit**: Instant (0ms)
- **File size**: 50-200KB per message
- **Format**: WAV, 16kHz, mono
- **Quality**: High (neural TTS)

## ✨ What Makes This Special

1. **Fully Local** - No cloud APIs, no costs, no limits
2. **High Quality** - Piper uses neural networks for natural speech
3. **Fast** - Caching makes repeat phrases instant
4. **Integrated** - Works seamlessly with memory, context, multi-agent
5. **Automatic** - Zero configuration needed, just works!

## 🎉 Success Checklist

- [ ] Browser shows "🔊 TTS Enabled" badge
- [ ] Character created successfully
- [ ] Sent a message to character
- [ ] 🔊 Play button appeared on response
- [ ] Audio played automatically
- [ ] Can click Play button to replay
- [ ] Console shows "Playing audio" message
- [ ] WAV files in `/audio_cache/` directory

If all checked, **TTS is working perfectly!** 🎊

## 🆘 Still Having Issues?

1. **Full system restart**:
   ```bash
   cd /Users/wilder/dev/RPGAI
   docker-compose down
   docker-compose up -d
   ```

2. **Hard refresh browser**: `Cmd+Shift+R`

3. **Check TTS_TESTING_GUIDE.md** for detailed troubleshooting

4. **View logs**:
   ```bash
   docker-compose logs backend --tail 50
   docker-compose logs piper --tail 20
   ```

## 📚 Documentation

- [TTS_TESTING_GUIDE.md](TTS_TESTING_GUIDE.md) - Detailed testing guide
- [MULTI_AGENT_GUIDE.md](MULTI_AGENT_GUIDE.md) - Multi-agent features
- [GAME_CONTEXT_GUIDE.md](GAME_CONTEXT_GUIDE.md) - Game context integration
- [UNREAL_INTEGRATION.md](UNREAL_INTEGRATION.md) - Unreal Engine integration

---

**Ready to test? Go to http://localhost:4020 and try it out!** 🚀
